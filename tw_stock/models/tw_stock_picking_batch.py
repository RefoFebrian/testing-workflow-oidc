# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import Counter, defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
from datetime import date

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
import logging
_logger = logging.getLogger(__name__)

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"
    _description = "Stock Picking Batch"
    _order = "create_date desc"
    
    # 7: defaults methods

    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state

    # 8: fields
    name = fields.Char(string='Batch Transfer', default='New', copy=False, compute='_compute_name', store=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    type = fields.Selection(selection=[('MD', 'MD'), ('Retail', 'Retail')], default='MD')
    date = fields.Date(string='Date', required=True, default=date.today())
    branch_type = fields.Char(related='company_id.branch_type_id.value', string='Branch Type', readonly=True)
    use_create_lots = fields.Boolean(related='picking_type_id.use_create_lots', string='Use Create Lots', readonly=True)
    is_validate_batch_line = fields.Boolean(related='picking_type_id.is_validate_batch_line', string='Validate Batch Line', readonly=True)
    is_need_location = fields.Boolean(related='picking_type_id.is_need_location', string='Need Location', readonly=True)
    default_qty = fields.Selection(related='picking_type_id.default_qty', string='Default Qty', readonly=True)
    has_batch_line = fields.Boolean(string='Has Batch Line', default=False)
    is_without_source = fields.Boolean('Is Without selecting source picking', default=False)

    # Audit Trail
    validate_date = fields.Datetime(string='Validate Date', help='Tanggal Validasi')
    validate_uid = fields.Many2one(comodel_name='res.users', string='Validate User', help='User yang melakukan validasi')

    # 9: relation fields
    domain_result_package_ids = fields.Many2many('stock.quant.package', 'stock_picking_batch_result_package_rel', 'batch_id', 'package_id', string='Domain Result Package', compute='_compute_domain_result_package_id')
    domain_product_ids = fields.Many2many('product.product', 'stock_picking_batch_product_rel', 'batch_id', 'product_id', string='Domain Product', compute='_compute_domain_product_id')
    result_package_id = fields.Many2one(comodel_name='stock.quant.package', string='Scan Package Number', help='Scan Package Number for the operation')
    product_id = fields.Many2one(comodel_name='product.product', string='Scan Product Code', help='Scan Product Code for the operation')
    location_id = fields.Many2one(comodel_name='stock.location', string="Location", help='Destination Location for the operation')
    batch_line_ids = fields.One2many(comodel_name='tw.stock.picking.batch.line', inverse_name="batch_id", string="Batch Line", domain=[('division', '!=', 'Extras')], help="Batch Line for the operation")
    source_picking_ids = fields.Many2many(comodel_name='stock.picking', string="Source Document", help="Document for the operation")
    batch_next_id = fields.Many2one(comodel_name='stock.picking.batch', string="Next Batch", help="Next Batch for the operation")
    batch_backorder_id = fields.Many2one(comodel_name='stock.picking.batch', string="Backorder Batch", help="Backorder Batch for the operation")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id', 'picking_type_id')
    def _compute_name(self):
        for record in self:
            branch_obj = record.company_id
            
            sequence_code = 'BATCH'
            if record.picking_type_id and record.picking_type_id.batch_sequence_code:
                sequence_code = record.picking_type_id.batch_sequence_code

            seq_name = self.env['ir.sequence'].with_company(branch_obj).get_sequence_code(sequence_code, branch_obj.code)
            record.name = seq_name

    @api.depends('company_id', 'picking_type_id', 'state')
    def _compute_allowed_picking_ids(self):
        """
            Replace method _compute_allowed_picking_ids dari model stock.picking.batch,
            untuk manghandle auto batch dari picking.
            Menambahkan state 'stored' sebagai allowed state untuk picking.
            Sehingga picking dengan state 'stored' dapat ditambahkan ke dalam batch.
        """
        allowed_picking_states = ['waiting', 'confirmed', 'assigned', 'stored']

        for batch in self:
            domain_states = list(allowed_picking_states)
            # Allows to add draft pickings only if batch is in draft as well.
            if batch.state == 'draft':
                domain_states.append('draft')
            domain = [
                ('company_id', '=', batch.company_id.id),
                ('state', 'in', domain_states),
            ]
            if batch.picking_type_id:
                domain += [('picking_type_id', '=', batch.picking_type_id.id)]
            batch.allowed_picking_ids = self.env['stock.picking'].search(domain)
    
    @api.depends('picking_ids')
    def _compute_domain_result_package_id(self):
        for record in self:
            record.domain_result_package_ids = False
            if record.picking_ids:
                record.domain_result_package_ids = record.picking_ids.mapped('move_line_ids').mapped('result_package_id')

    @api.depends('picking_ids', 'result_package_id')
    def _compute_domain_product_id(self):
        for record in self:
            record.domain_product_ids = False
            if record.picking_ids and record.result_package_id:
                record.domain_product_ids = record.picking_ids.mapped('move_line_ids').filtered(lambda ml: ml.result_package_id == record.result_package_id).mapped('product_id')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Reset and resolve picking_type_id when company changes.

        Resolves picking_type_id dynamically based on context keys:
        - sequence_code: sequence code of the picking type (e.g. 'IN', 'QC', 'STOR')
        - default_division: division filter (e.g. 'Sparepart', 'Unit')

        This approach is used because picking_type_id cannot be hard-coded in XML
        since it is auto-generated per warehouse and varies across databases.
        """
        self.picking_type_id = False
        if not self.company_id:
            return
        sequence_code = self._context.get('sequence_code')
        division = self._context.get('default_division')
        if sequence_code and division:
            picking_type = self._resolve_picking_type_by_sequence(
                self.company_id.id, sequence_code, division
            )
            if picking_type:
                self.picking_type_id = picking_type.id

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        self.source_picking_ids = False

    @api.onchange('source_picking_ids')
    def _onchange_source_picking_ids(self):
        """Synchronize batch_line_ids with source_picking_ids.

        Handles two scenarios:
        1. Auto-create mode (is_auto_create_batch_line=True): Full recompute —
           clear all existing batch lines and rebuild from current source_picking_ids.
           This prevents duplicates when adding pickings.
        2. Manual mode: Remove only batch lines whose picking was removed
           from source_picking_ids, keeping manually added lines intact.
        """
        if self.is_without_source:
            return
        
        if not self.source_picking_ids:
            self.batch_line_ids = [(5, 0, 0)]
            return

        if self.picking_type_id.is_auto_create_batch_line:
            # Full recompute: (5,0,0) clears all existing lines, then rebuild
            batch_lines = [(5, 0, 0)]
            for picking in self.source_picking_ids:
                for move in picking.move_ids:
                    if not move.move_line_ids:
                        move._origin._action_assign()
                    
                    quant_obj = move._get_location_from_stock_avb(picking, move.product_id.id)
                    for move_line in move.move_line_ids:
                        vals = {
                            'move_id': move_line.move_id.id,
                            'product_id': move_line.product_id.id,
                            'quantity': move_line.quantity,
                            'product_uom_qty': move_line.move_id.product_uom_qty,
                            'location_id': move_line.location_id.id,
                            'location_dest_id': move_line.location_dest_id.id,
                        }
                        if move_line.lot_id:
                            vals['lot_id'] = move_line.lot_id.id
                        if move_line.lot_name:
                            vals['lot_name'] = move_line.lot_name

                        if quant_obj:
                            if picking.picking_type_id.sequence_code in ('PICK', 'OUT'):
                                vals['location_id'] = quant_obj.location_id.id

                            if picking.picking_type_id.code == 'incoming':
                                vals['location_dest_id'] = quant_obj.location_id.id

                        batch_lines.append((0, 0, vals))

            self.batch_line_ids = batch_lines
        else:
            # Manual mode: remove lines whose picking is no longer in source_picking_ids
            # Filter on virtual recordset directly (never use write() inside onchange)
            self.batch_line_ids = self.batch_line_ids.filtered(
                lambda x: not x.move_id or x.move_id.picking_id.id in self.source_picking_ids.ids
            )

    @api.onchange('batch_line_ids')
    def _onchange_validate_duplicate_lot(self):
        """Validate duplicate lot_id in batch_line_ids."""
        if not self.batch_line_ids:
            return
        
        seen_lot_ids = {}
        for line in self.batch_line_ids:
            if line.lot_id:
                if line.lot_id.id in seen_lot_ids:
                    return {
                        'warning': {
                            'title': _("Warning"),
                            'message': _(f"Unit dengan serial number '{line.lot_id.name}' sudah di input.\nMohon pilih serial number lain."),
                        }
                    }
                seen_lot_ids[line.lot_id.id] = True

    @api.onchange('batch_line_ids')
    def _onchange_batch_line_ids_moves(self):
        """Assign move_id centrally for Retail batches based on lines."""    
        if hasattr(self, '_origin') and self._origin:
            source_picking_ids = self._origin.source_picking_ids
        else:
            source_picking_ids = self.source_picking_ids
        
        if not source_picking_ids or self.is_without_source:
            if self.batch_line_ids:
                self.is_without_source = True
            if self.type == 'MD' and self.division == 'Unit':
                for line in self.batch_line_ids.filtered(lambda x: not x.move_id and x.lot_id):
                    if hasattr(line.lot_id, 'ship_list_number'):
                        ship_list_numbers = line.lot_id.ship_list_number
                        move_objs = self.env['stock.move'].search([
                            ('product_id','=',line.product_id.id),
                            ('picking_id.mft_reference', '=', ship_list_numbers),
                            ('picking_type_id', '=', self.picking_type_id.id),
                            ('state', 'in', ['assigned', 'confirmed', 'waiting'])
                        ])
                        source_picking_ids |= move_objs.mapped('picking_id')
                        self.source_picking_ids |= source_picking_ids
            
        if source_picking_ids:
            used_moves_qty = {}
            # First pass: Count already matched moves
            for line in self.batch_line_ids:
                if line.move_id:
                    mid = line.move_id.id
                    if isinstance(mid, models.NewId):
                        mid = line.move_id._origin.id if hasattr(line.move_id, '_origin') and line.move_id._origin else getattr(line.move_id, 'id', 0)
                    if mid:
                        used_moves_qty[mid] = used_moves_qty.get(mid, 0) + max(line.quantity, 1)

            # Second pass: Assign available moves to lines missing move_id
            for line in self.batch_line_ids:
                if line.product_id and not line.move_id:
                    search_move = [
                        ('picking_id', 'in', source_picking_ids.ids),
                        ('product_id', '=', line.product_id.id),
                        ('state', 'in', ['assigned', 'confirmed', 'waiting'])
                    ]
                    if self.type == 'MD' and self.division == 'Unit' and hasattr(line.lot_id, 'ship_list_number'):
                        search_move.append(('picking_id.mft_reference', '=', line.lot_id.ship_list_number))
                        
                    move_objs = self.env['stock.move'].search(search_move)
                    if move_objs:
                        available_moves = [move for move in move_objs if used_moves_qty.get(move.id, 0) < move.product_uom_qty]

                        if available_moves:
                            available_moves.sort(key=lambda m: used_moves_qty.get(m.id, 0))
                            selected_move = available_moves[0]
                            used_qty = used_moves_qty.get(selected_move.id, 0)
                            line.move_id = selected_move.id
                            line.location_id = selected_move.location_id.id
                            line.product_uom_qty = selected_move.product_uom_qty
                            qty_batch_line = selected_move.product_uom_qty - used_qty if selected_move.product_id.product_tmpl_id.tracking != 'serial' else 1
                            line.quantity = qty_batch_line if self.default_qty == 'auto' else 0
                            used_moves_qty[selected_move.id] = used_moves_qty.get(selected_move.id, 0) + max(line.quantity, 1)
                        else:
                            return {
                                'warning': {
                                    'title': _("Warning"),
                                    'message': _("Move untuk produk %s sudah terpakai semua", line.product_id.name),
                                }
                            }
        
    @api.onchange('batch_line_ids')
    def _onchange_batch_line_ids_sequence(self):
        """Update sequence_number for each line based on its position in the list."""
        for i, line in enumerate(self.batch_line_ids, start=1):
            line.sequence_number = i

    @api.onchange('result_package_id')
    def _onchange_result_package_id(self):
        self.product_id = False
            
    @api.depends('picking_type_id')
    def _compute_location_id(self):
        for picking in self:
            picking.picking_type_id = picking.picking_type_id.get_picking_type('incoming', picking.company_id.id)
    
    @api.depends('picking_ids', 'picking_ids.move_line_ids', 'batch_line_ids.lot_id', 'batch_line_ids.lot_name')
    def _compute_move_line_ids(self):
        super(InheritStockPickingBatch, self)._compute_move_line_ids()
        for batch in self:
            if not batch.batch_line_ids:
                batch.move_line_ids = batch.picking_ids.move_line_ids
            else:
                batch_lot_ids = batch.batch_line_ids.mapped('lot_id')
                matching_move_lines = batch.picking_ids.move_line_ids.filtered(
                    lambda ml: ml.lot_id in batch_lot_ids or ml.lot_name or (ml.move_id.division == 'Sparepart' and ml.quantity > 0)
                )
                batch.move_line_ids = matching_move_lines

    @api.depends('picking_ids', 'picking_ids.move_ids', 'picking_ids.move_ids.state', 'move_line_ids')
    def _compute_move_ids(self):
        super(InheritStockPickingBatch, self)._compute_move_ids()
        for batch in self:
            if not batch.batch_line_ids:
                batch.move_ids = batch.picking_ids.move_ids
            else:
                batch.move_ids = batch.move_line_ids.mapped('move_id')
            
            batch.show_check_availability = any(
                m.state not in ['assigned', 'cancel', 'done'] 
                for m in batch.move_ids
            )

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        return super(InheritStockPickingBatch, self).create(vals_list)
        
    def write(self, vals):
        return super(InheritStockPickingBatch, self).write(vals)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning(_("Batch Transfer can not be removed unless the state is draft!"))
            
        return super().unlink()

    # 13: action methods
    def action_confirm(self, auto_confirm=False):
        """
        Confirm the batch picking.
        
        This method validates prerequisites, checks for duplicates, processes
        batch lines based on division type, and performs cleanup operations.
        """
        self.ensure_one()
        # Jika batch (auto-created), langsung confirm tanpa cleanup dan processing
        if auto_confirm:
            return super(InheritStockPickingBatch, self).action_confirm()
        
        # Step 1: Validate prerequisites
        self._validate_confirm_prerequisites()
        
        # Step 2: Cleanup Removeable Lines
        self._cleanup_removeable_all_move_lines()
        
        # Step 3: Process lines by type
        picking_ids = self._process_batch_lines()
        
        # Step 4: Hook for additional processing (e.g. extras in tw_stock_extras)
        self._process_after_batch_lines(picking_ids)
        
        res = super(InheritStockPickingBatch, self).action_confirm()

        if self.is_validate_batch_line and self.batch_line_ids:
            self.batch_line_ids.sudo().unlink()
        
        return res

    def action_done(self):
        self.ensure_one()
        
        # Re-clean and re-process batch lines to recover from any "Check Availability" resets
        # self._cleanup_removeable_all_move_lines()
        # picking_ids = self._process_batch_lines()
        # self._process_after_batch_lines(picking_ids)

        if self.is_validate_batch_line:
            batch_qtys = defaultdict(float)
            for line in self.batch_line_ids:
                if line.product_id:
                    batch_qtys[line.product_id.id] += line.quantity

            move_qtys = defaultdict(float)
            if self.is_need_location:
                for ml in self.move_line_ids:
                    if ml.product_id:
                        move_qtys[ml.product_id.id] += ml.quantity
            else:
                for move in self.picking_ids.move_ids.filtered(lambda m: m.state not in ['cancel']):
                    if move.product_id:
                        move_qtys[move.product_id.id] += move.product_uom_qty

            all_product_ids = set(batch_qtys.keys()) | set(move_qtys.keys())
            mismatches = []
            
            for product_id in all_product_ids:
                b_qty = batch_qtys.get(product_id, 0.0)
                m_qty = move_qtys.get(product_id, 0.0)
                product = self.env['product.product'].browse(product_id)
                uom = product.uom_id
                precision = uom.rounding if uom else 0.01
                if float_compare(b_qty, m_qty, precision_rounding=precision) != 0:
                    compare_label = _("Detail Line") if self.is_need_location else _("Qty Request")
                    mismatches.append(
                        _("- %s: Pick/Pack Line = %s, %s = %s") % (product.default_code, b_qty, compare_label, m_qty)
                    )

            if mismatches:
                compare_label = _("Detail Line") if self.is_need_location else _("Qty Request")
                raise Warning(
                    _("Terdapat perbedaan antara produk/kuantitas pada Pick/Pack Line dengan %s:\n%s") 
                    % (compare_label, "\n".join(mismatches))
                )
        
        # Validasi & Update Quantity sebelum Odoo memproses action_done (agar tidak error pemecahan package)
        company_warehouse = self.env['stock.warehouse']._get_company_warehouse(self.company_id)
        qc_move_lines = self.move_line_ids.filtered(lambda ml: ml.location_id.id == company_warehouse.wh_input_stock_loc_id.id)
        if qc_move_lines:
            total_supply_qty = sum(qc_move_lines.mapped('supply_qty'))
            if total_supply_qty <= 0:
                raise Warning("Harap lakukan Quality Checking terlebih dahulu, dengan cara scan nomor kardus dan kode produk kemudian klik tombol search!")
        
        for move_line in self.move_line_ids:
            if move_line.location_id.id == company_warehouse.wh_input_stock_loc_id.id:
                if move_line.supply_qty <= 0:
                    raise Warning(f"Sparepart {move_line.product_id.default_code} pada nomor kardus {move_line.result_package_id.name} belum di lakukan Quality Check!")

            if move_line.supply_qty > 0:
                move_line.sudo().write({'quantity': move_line.supply_qty})
            
            if move_line.location_id.id == company_warehouse.wh_qc_stock_loc_id.id and move_line.location_qc_id and move_line.location_dest_id.id != move_line.location_qc_id.id:
                move_line.sudo().write({'location_dest_id': move_line.location_qc_id.id})
                
            if move_line.result_package_id and move_line.location_id.usage in ['internal', 'transit']:
                # Ambil semua line dari batch ini yang mengacu ke kardus yang sama
                package_lines = self.move_line_ids.filtered(lambda ml: ml.result_package_id.id == move_line.result_package_id.id)
                total_supplied = sum(package_lines.mapped('quantity'))
                
                # Jumlah total fisik aktual dari kardus tersebut di lokasi sumber
                package_quants = move_line.result_package_id.quant_ids.filtered(lambda q: q.location_id.id == move_line.location_id.id)
                total_in_package = sum(package_quants.mapped('quantity'))
                
                # Cek apakah arah lokasinya dipecah
                dest_locations = package_lines.mapped('location_dest_id')
                
                # Skenario Wajib Unpack:
                # 1. total_in_package == 0 (Kardus fisik tidak ditemukan di lokasi sumber akibat test data usang)
                # 2. total_supplied < total_in_package (Hanya lulus QC sebagian/dipecah isinya)
                # 3. len(dest_locations) > 1 (Pergi ke beda-beda Rak walaupun 1 kardus)
                if total_in_package == 0 or total_supplied < total_in_package or len(dest_locations) > 1:
                    move_line.sudo().write({'result_package_id': False})

        res = super(InheritStockPickingBatch, self).action_done()
        self._process_create_batch_next_step()
        self._process_create_batch_for_backorder()
        return res
    
    def action_process_quality_check(self):
        self.ensure_one()
        if self.product_id:
            if not self.result_package_id:
                raise Warning("Mohon scan nomor kardus terlebih dahulu.")
            
            move_line_obj = self.move_line_ids.filtered(lambda ml: ml.result_package_id.id == self.result_package_id.id and ml.product_id.id == self.product_id.id)
            if move_line_obj:
                self.result_package_id = False
                self.product_id = False

                form_id = self.env.ref('tw_stock.tw_stock_quality_check_incoming_form_view').id
                return {
                    'name': 'Quality Check',
                    'res_model': 'tw.stock.quality.check.incoming',
                    'type': 'ir.actions.act_window',
                    'view_id': form_id,
                    'views': [(form_id, 'form')],
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_company_id': self.company_id.id,
                        'default_picking_id': move_line_obj.picking_id.id,
                        'default_move_line_id': move_line_obj.id,
                        'default_result_package_id': move_line_obj.result_package_id.id,
                        'default_product_id': move_line_obj.product_id.id,
                        'default_location_dest_id': move_line_obj.location_qc_id.id if move_line_obj.location_qc_id else move_line_obj.location_dest_id.id,
                        'default_lot_id': move_line_obj.lot_id.id,
                        'default_initial_quantity': move_line_obj.quantity,
                    }
                }
            else:
                raise Warning(f"Product dengan code '{self.product_id.default_code}' tidak ditemukan.")

    def action_generate_line(self):
        self.ensure_one()
        if self.source_picking_ids and self.division == 'Sparepart':
            package_obj = self.env['stock.quant.package'].suspend_security().search([
                ('picking_id', 'in', self.source_picking_ids.ids)
            ])
            if package_obj:
                line_ids = []
                package_numbers = []
                sequence_numbers = 0
                for package in package_obj:
                    existing_package_ids = [rec.package_number for rec in self.batch_line_ids]
                    if package.name not in existing_package_ids and package.name not in package_numbers:
                        package_numbers.append(package.name)
                        sequence_numbers += 1
                        line_ids.append((0, 0, {
                            'package_number': package.name,
                            'sequence_number': sequence_numbers
                        }))
                    
                if line_ids:
                    self.batch_line_ids = line_ids
            else:
                raise Warning(f"Package Number not found in {', '.join(self.source_picking_ids.mapped('name'))}!")
    
    def action_view_pickings(self):
        """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
        """
        self.ensure_one()
        pickings = self.picking_ids
        result = self.env["ir.actions.actions"]._for_xml_id('stock.action_picking_tree_all')
        # choose the view_mode accordingly
        if not pickings or len(pickings) > 1:
            result['domain'] = [('id', 'in', pickings.ids)]
        elif len(pickings) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if view != 'form']
            result['res_id'] = pickings.id
        return result

    def action_print_travel_document(self):
        self.ensure_one()
        return self.env.ref('tw_stock.batch_travel_document_stock_picking_batch_report').report_action(self.id)

    def action_batch_goods_receipt_report(self):
        self.ensure_one()
        return self.env.ref('tw_stock.batch_goods_receipt_report').report_action(self.id)

    def action_batch_bastk_report(self):
        self.ensure_one()
        return self.env.ref('tw_stock.batch_bastk_document_report').report_action(self.id)

    def action_cancel(self):
        for record in self:
            if record.type == 'MD' and record.division == 'Sparepart':
                pickings = record.picking_ids.filtered(lambda x: x.state not in ['done', 'cancel'])
                if pickings:
                    move_lines = pickings.mapped('move_ids_without_package.move_line_ids')
                    if move_lines:
                        move_lines.write({'quantity': 0})
            else:
                picking_obj = self.env['stock.picking'].suspend_security().search([
                    ('batch_id', '=', record.id),
                    ('state', 'not in', ['done', 'cancel']),
                ])
                if picking_obj:
                    move_lines = picking_obj.mapped('move_ids_without_package.move_line_ids')
                    additional_move_lines = self._additional_cancelable_lines(picking_obj)
                    all_move_lines = move_lines | additional_move_lines
                    if all_move_lines:
                        all_move_lines.write({'is_removeable': True})
                        all_move_lines.suspend_security().unlink()
            
        return super(InheritStockPickingBatch, self).action_cancel()
    
    def action_set_draft(self):
        self.state = 'draft'
    
    def action_view_next_batch(self):
        self.ensure_one()
        form_view_id = self.env.ref('tw_stock.tw_stock_picking_batch_original_form_view').id
        if self.batch_next_id.picking_type_id.sequence_code in ('QC', 'STOR'):
            form_view_id = self.env.ref('tw_stock.tw_stock_picking_batch_quality_check_form').id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking.batch',
            'res_id': self.batch_next_id.id,
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'context': {
                'default_division': self.division,
                'sequence_code': self.batch_next_id.picking_type_id.sequence_code
            }
        }
        
    def action_view_backorder_batch(self):
        self.ensure_one()
        form_view_id = self.env.ref('tw_stock.tw_stock_picking_batch_original_form_view').id
        if self.batch_backorder_id.picking_type_id.sequence_code in ('QC', 'STOR'):
            form_view_id = self.env.ref('tw_stock.tw_stock_picking_batch_quality_check_form').id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking.batch',
            'res_id': self.batch_backorder_id.id,
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'context': {
                'default_division': self.division,
                'sequence_code': self.batch_backorder_id.picking_type_id.sequence_code
            }
        }

    # 14: private methods
    def _resolve_picking_type_by_sequence(self, company_id, sequence_code, division):
        """Resolve picking type by sequence code, company, and division.

        Searches for a picking type matching the given criteria within the
        company's warehouse. Falls back to search without division filter.

        Args:
            company_id: res.company record ID
            sequence_code: picking type sequence code (e.g. 'IN', 'QC', 'STOR')
            division: division filter (e.g. 'Sparepart', 'Unit')

        Returns:
            stock.picking.type recordset (single record or empty)
        """
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', company_id)], limit=1
        )
        if not warehouse:
            return self.env['stock.picking.type']
        picking_type = self.env['stock.picking.type'].search([
            ('sequence_code', '=', sequence_code),
            ('warehouse_id', '=', warehouse.id),
            ('division', '=', division),
        ], limit=1)
        # Fallback: search tanpa filter division
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([
                ('sequence_code', '=', sequence_code),
                ('warehouse_id', '=', warehouse.id),
            ], limit=1)
        return picking_type

    def _process_create_batch_next_step(self):
        """Create next step batch and propagate custom move line values.
        
        Follows Odoo 18 base pattern:
        1. Create batch with next step pickings
        2. Confirm and assign (creates move lines via _action_assign)
        3. Propagate custom fields (location_qc_id, supply_qty) from origin move lines
        """
        picking_ids = self._get_picking_next_transfer()
        if not picking_ids:
            return

        # Group pickings by picking_type_id — one batch per operation type
        pickings = self.env['stock.picking'].browse(picking_ids)
        groups = {}
        for picking in pickings:
            pt_id = picking.picking_type_id.id
            groups.setdefault(pt_id, []).append(picking.id)

        for picking_type_id, grouped_ids in groups.items():
            new_batch_vals = self._prepare_create_batch_vals(grouped_ids, picking_type_id)
            new_batch = self.env['stock.picking.batch'].sudo().create(new_batch_vals)
            new_batch.sudo().action_confirm(auto_confirm=True)
            new_batch.sudo().action_assign()
            self.sudo().write({'batch_next_id': new_batch.id})
            self._propagate_move_line_custom_values(new_batch)

    def _process_create_batch_for_backorder(self):
        backorder_picking_obj = self.env['stock.picking'].search([
            ('backorder_id', 'in', self.picking_ids.ids),
            ('picking_type_id.is_create_batch_backorder', '=', True),
            ('state', 'in', ['assigned', 'confirmed', 'waiting']),
        ])
        if backorder_picking_obj:
            picking_type_id = backorder_picking_obj[0].picking_type_id.id
            new_batch_vals = self._prepare_create_batch_vals(backorder_picking_obj.ids, picking_type_id)
            new_batch = self.env['stock.picking.batch'].sudo().create(new_batch_vals)
            new_batch.sudo().action_confirm(auto_confirm=True)
            new_batch.sudo().action_assign()
            self.sudo().write({'batch_backorder_id': new_batch.id})
            self._propagate_move_line_custom_values(new_batch)
    
    def _prepare_create_batch_vals(self, picking_ids, picking_type_id):
        vals = {
            'company_id': self.company_id.id,
            'picking_type_id': picking_type_id,
            'type': self.type,
            'division': self.division,
            'source_picking_ids': [(6, 0, picking_ids)],
            'picking_ids': [(6, 0, picking_ids)],
        }
        return vals

    def _propagate_move_line_custom_values(self, next_batch):
        """Propagate custom fields from current batch to next step batch.

        Propagated fields: location_qc_id, supply_qty, is_rfs.

        Two-pass matching strategy:

        Pass 1 — 1:1 matching (handles N:N and 1:1 cases):
          Priority 1: Chain match via move_orig_ids + exact key (product, package, lot)
          Priority 2: Chain match via move_orig_ids + product-only (for lines with custom values)
          Each origin move_line is consumed once (tracked via consumed_ml_ids).

        Pass 2 — N:1 aggregation (handles unpack / merge cases):
          After 1:1 matching, remaining unconsumed origin move_lines with the
          same product + chain are aggregated into the already-matched next_ml.
          This covers the scenario where multiple origin packages are partially
          received and unpacked, causing Odoo to consolidate them into fewer
          next-step move_lines.

        Aggregation rules:
        - supply_qty: summed across all matched origin move_lines
        - location_qc_id: taken from the first origin that has a value
        - is_rfs: False if ANY matched origin has is_rfs=False

        Key mapping between steps:
        - Step N move_line.result_package_id → Step N+1 move_line.package_id
        - Step N move_line.lot_id → Step N+1 move_line.lot_id
        - Step N move_line.product_id → Step N+1 move_line.product_id

        :param next_batch: stock.picking.batch record of the next step
        """
        if not next_batch.move_line_ids:
            return

        current_move_ids = set(self.move_ids.ids)

        # Build lookup: origin_move_id → [move_lines] from current batch
        origin_mls_by_move = defaultdict(list)
        for ml in self.move_line_ids:
            origin_mls_by_move[ml.move_id.id].append(ml)

        # Track consumed origin move lines
        consumed_ml_ids = set()

        # Store match results for Pass 2 aggregation: [(next_ml, [origin_mls], chained_move_ids)]
        match_results = []

        # ── Pass 1: 1:1 matching ──
        for next_ml in next_batch.move_line_ids:
            chained_move_ids = set(next_ml.move_id.move_orig_ids.ids) & current_move_ids
            if not chained_move_ids:
                continue

            origin_ml = None
            next_pkg_id = next_ml.package_id.id if next_ml.package_id else False
            next_lot_id = next_ml.lot_id.id if next_ml.lot_id else False

            # Priority 1: Exact match (product + package + lot) within chained moves
            for orig_move_id in chained_move_ids:
                for ml in origin_mls_by_move.get(orig_move_id, []):
                    if ml.id in consumed_ml_ids:
                        continue
                    orig_pkg_id = ml.result_package_id.id if ml.result_package_id else False
                    orig_lot_id = ml.lot_id.id if ml.lot_id else False
                    if (ml.product_id.id == next_ml.product_id.id
                            and orig_pkg_id == next_pkg_id
                            and orig_lot_id == next_lot_id):
                        origin_ml = ml
                        break
                if origin_ml:
                    break

            # Priority 2: Product-only match within chained moves (must have custom values)
            if not origin_ml:
                for orig_move_id in chained_move_ids:
                    for ml in origin_mls_by_move.get(orig_move_id, []):
                        if ml.id in consumed_ml_ids:
                            continue
                        if ml.product_id.id == next_ml.product_id.id and (
                            ml.location_qc_id or ml.supply_qty > 0 or not ml.is_rfs
                        ):
                            origin_ml = ml
                            break
                    if origin_ml:
                        break

            if not origin_ml:
                continue

            consumed_ml_ids.add(origin_ml.id)
            match_results.append((next_ml, [origin_ml], chained_move_ids))

        # ── Pass 2: Aggregate remaining unconsumed origin MLs (N:1 merge) ──
        # Covers scenario: multiple origin packages partially received → unpacked
        # → Odoo consolidates into fewer next-step move_lines.
        for _next_ml, matched_mls, chained_move_ids in match_results:
            product_id = _next_ml.product_id.id
            for orig_move_id in chained_move_ids:
                for ml in origin_mls_by_move.get(orig_move_id, []):
                    if ml.id in consumed_ml_ids:
                        continue
                    if ml.product_id.id == product_id:
                        matched_mls.append(ml)
                        consumed_ml_ids.add(ml.id)

        # ── Group & Split (Write aggregated values) ──
        for next_ml, matched_mls, _chained in match_results:
            if not matched_mls:
                continue

            # Group origin move lines by (location_qc_id, is_rfs)
            # This splits back out any lines Odoo accidentally merged despite custom differences
            groups = defaultdict(list)
            for ml in matched_mls:
                key = (ml.location_qc_id.id if ml.location_qc_id else False, ml.is_rfs)
                groups[key].append(ml)

            group_items = list(groups.items())

            # Group 1: update the existing next_ml
            first_key, first_mls = group_items[0]
            first_loc_qc_id, first_is_rfs = first_key
            
            first_qty = sum(ml.quantity for ml in first_mls)
            first_supply = sum(ml.supply_qty for ml in first_mls)

            vals = {}
            if first_loc_qc_id:
                vals['location_qc_id'] = first_loc_qc_id
            if first_supply > 0:
                vals['supply_qty'] = first_supply
            if not first_is_rfs:
                vals['is_rfs'] = False

            # If there are multiple groups, we MUST deduct the quantity of the first next_ml to split
            if len(group_items) > 1 and first_qty > 0:
                vals['quantity'] = first_qty

            if vals:
                next_ml.sudo().write(vals)

            # Subsequent Groups: split the original next_ml by copying it
            for key, mls in group_items[1:]:
                loc_qc_id, is_rfs = key
                qty = sum(ml.quantity for ml in mls)
                supply_qty = sum(ml.supply_qty for ml in mls)

                split_vals = {}
                if loc_qc_id:
                    split_vals['location_qc_id'] = loc_qc_id
                if supply_qty > 0:
                    split_vals['supply_qty'] = supply_qty
                if qty > 0:
                    split_vals['quantity'] = qty
                if not is_rfs:
                    split_vals['is_rfs'] = False

                if split_vals:
                    next_ml.sudo().copy(default=split_vals)
            
    def _validate_incoming_md_next_step(self, picking):
        """Validate picking if picking type is create batch next step and reception steps is not one step"""
        is_create_batch_next_step = picking.picking_type_id.is_create_batch_next_step
        if is_create_batch_next_step:
            warehouse_obj = self.env['stock.warehouse']._get_company_warehouse(picking.company_id)
            if warehouse_obj.reception_steps != 'one_step':
                return True
        return False

    def _get_picking_next_transfer(self):
        picking_ids = []
        for picking in self.picking_ids:
            if self._validate_incoming_md_next_step(picking):
                next_transfer_picking = picking._get_next_transfers()
                if next_transfer_picking:
                    picking_ids.extend(next_transfer_picking.ids)
        return picking_ids
        
    def _process_after_batch_lines(self, picking_ids):
        """Hook for additional processing after batch lines.
        
        Override this method in other modules to add processing
        between process_batch_lines and Odoo base action_confirm.
        
        :param picking_ids: list of picking ids from process_batch_lines
        """
        if not self.picking_ids:
            self.picking_ids = picking_ids

    def _additional_cancelable_lines(self, picking_obj=False):
        """Process cancelable lines."""
        return self.env['stock.move.line']

    def _validate_confirm_prerequisites(self):
        """Validate state before confirm."""
        if self.state != 'draft':
            raise Warning(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        
        for line in self.batch_line_ids:
            # Default tracking ('serial', 'lot') atau custom tracking ('serial_chassis')
            is_tracked = False
            if line.categ_tracking in ('serial', 'serial_chassis'):
                is_tracked = True
            elif line.product_id.tracking in ('serial', 'lot'):
                is_tracked = True
            
            if self.source_picking_ids and line.product_id and not line.move_id:
                raise Warning(_("Permintaan Validasi Ditolak!\nProduk '%s' memerlukan input Move, namun belum ditentukan.", line.product_id.display_name))

            if is_tracked:
                if not line.lot_id and not line.lot_name:
                    raise Warning(_("Permintaan Validasi Ditolak!\nProduk '%s' memerlukan input Serial Number / Lot, namun belum ditentukan.", line.product_id.display_name))
                
        self._validate_duplicate_serials()

    def _validate_duplicate_serials(self):
        """Check for duplicate serial numbers in batch lines."""
        serials = [line.lot_id.name for line in self.batch_line_ids if line.lot_id]
        if not serials:
            return
        
        # Use Counter for O(n) duplicate detection instead of O(n²)
        serial_counts = Counter(serials)
        duplicates = {s for s, count in serial_counts.items() if count > 1}
        if duplicates:
            raise Warning(f"Duplicate Serial Numbers: {', '.join(duplicates)}")

    def _process_batch_lines(self):
        """
        Process all batch lines and return picking IDs.
        
        Handles three types of lines based on division:
        - Sparepart lines: processed when division is Sparepart
        - Unit lines: processed when division is Unit and no move_id
        - Move lines: processed when line has move_id
        
        :return: list of processed picking ids
        """
        picking_ids = []
        batch_lines = self.batch_line_ids
        
        if not batch_lines:
            return picking_ids
        
        # Process Sparepart lines (with package_number) - hanya berlaku untuk penerimaan sparepart MD dari AHM karena package_number hanya digunakan untuk penerimaan MD dari AHM
        if self.division == 'Sparepart' and self.type == 'MD':
            sparepart_lines = batch_lines.filtered(lambda line: line.package_number)
            if sparepart_lines:
                picking_ids.extend(self._process_confirm_sparepart_lines(sparepart_lines))
        # Process Unit lines (without move_id) - hanya berlaku untuk penerimaan unit MD dari AHM karena lines yang memiliki move_id sudah pasti itu bukan berasal dari penerimaan MD dari AHM
        elif self.division == 'Unit' and self.type == 'MD':
            unit_lines = batch_lines.filtered(lambda line: line.lot_id)
            if unit_lines:
                picking_ids.extend(self._process_confirm_unit_lines(unit_lines))
        elif self.type == 'Retail':
            # Process Move lines (with move_id) - applies to all divisions (setiap proses selain penerimaan MD dari AHM, selalu mempunyai move_id)
            move_lines_with_move_id = batch_lines.filtered(lambda line: line.move_id)
            if move_lines_with_move_id:
                self._process_confirm_move_lines(move_lines_with_move_id)
                if self.division == 'Unit':
                    picking_ids.extend(self.source_picking_ids.ids)
        
        return picking_ids

    def _process_confirm_sparepart_lines(self, sparepart_lines):
        """
        Process sparepart lines in the batch.
        
        Steps:
        1. Validate duplicate package numbers
        2. Find packages and their move lines
        3. Update move lines with quantity and location
        4. Link pickings to batch
        5. Mark unused move lines as removeable
        
        :param sparepart_lines: recordset of tw.stock.picking.batch.line with package_number
        :return: None
        """
        packages = sparepart_lines.mapped('package_number')
        
        # Step 1: Validate duplicates using O(n) Counter
        self._validate_duplicate_packages(packages)
        
        # Step 2: Process each package
        search = [
            ('name', 'in', packages),
            ('current_quantity', '>', 0)
        ]
        if self.source_picking_ids:
            search.append(('picking_id', 'in', self.source_picking_ids.ids))
        package_obj = self.env['stock.quant.package'].suspend_security().search(search)

        picking_ids = []
        for package in package_obj:
            picking_ids.extend(self._process_single_package(package))
        
        # Step 3: Mark unused move lines as removeable and delete it
        self._mark_sparepart_lines_removeable(package_obj)
        self._cleanup_removeable_all_move_lines()
        return picking_ids

    def _validate_duplicate_packages(self, packages):
        """
        Check for duplicate package numbers.
        
        :param packages: list of package number strings
        :raises Warning: if duplicate package numbers found
        """
        package_counts = Counter(packages)
        duplicates = {p for p, count in package_counts.items() if count > 1}
        if duplicates:
            raise Warning(f"Duplicate Package Numbers: {', '.join(duplicates)}")

    def _process_single_package(self, package):
        """
        Process a single package for sparepart confirmation.
        
        :param package: stock.quant.package record
        """
        # Find move line for this package
        move_line = self._get_move_line_for_package(package)
        
        # Prepare and update move line values
        move_line_vals = self._prepare_sparepart_move_line_vals(package, move_line)
        if isinstance(move_line_vals, list):
            move_line.sudo().write({'is_removeable': True})
            self.env['stock.move.line'].sudo().create(move_line_vals)
        else:
            move_line.sudo().write(move_line_vals)
        
        # Link picking to batch if not already linked
        if not move_line.picking_id.batch_id:
            picking_vals = self._prepare_batch_picking_vals()
            move_line.picking_id.suspend_security().write(picking_vals)
        return [move_line.picking_id.id]

    def _get_lot_ids(self):
        for record in self:
            search_lot = [('company_id', '=', record.company_id.id)]
            if record.source_picking_ids:
                if record.type == 'MD' and record.division == 'Unit':
                    source_document = [rec.mft_reference for rec in record.source_picking_ids if getattr(rec, 'mft_reference', False)]
                    if source_document:
                        search_lot.extend([('ship_list_number', 'in', source_document), ('state', '=', 'intransit')])
                    else:
                        search_lot.append(('state', '=', 'intransit'))
                else:
                    search_lot.append(('state', '=', 'stock'))
            else:
                search_lot.append(('state', '=', 'intransit'))
            
            lot_ids = self.env['stock.lot'].suspend_security().search(search_lot)
            return lot_ids

    def _get_move_line_for_package(self, package):
        """
        Get move line for a package or raise error if not found.
        
        :param package: stock.quant.package record
        :return: stock.move.line record
        :raises Warning: if move line not found or already processed
        """

        search = [
            ('result_package_id', '=', package.id),
            ('picking_id', '=', package.picking_id.id),
            ('product_id', '=', package.product_id.id),
        ]
        if self.source_picking_ids:
            search.append(('picking_id', 'in', self.source_picking_ids.ids))
        move_line = self.env['stock.move.line'].suspend_security().search(search, limit=1)
        if not move_line:
            raise Warning(f"Move Line with Package {package.name} Not Found or Already processed in Picking!")
        return move_line

    def _prepare_sparepart_move_line_vals(self, package, move_line):
        """
        Prepare values for sparepart move line update.
        
        :param package: stock.quant.package record
        :param move_line: stock.move.line record
        :return: dict of values to write
        """
        move_line_vals = []
        if package.product_id.product_tmpl_id.tracking != 'serial':
            move_line_vals = {
                'quantity': package.current_quantity,
                'is_removeable': False,
                'picked': True,
            }
            
            if self.location_id:
                move_line_vals['location_qc_id'] = self.location_id.id
            else:
                quant_obj = move_line.move_id._get_location_from_stock_avb(
                    move_line.picking_id, package.product_id.id
                )
                if quant_obj:
                    move_line_vals['location_qc_id'] = quant_obj.location_id.id
        else:
            for rec in range(package.current_quantity):
                move_line_vals.append({
                    'company_id': package.company_id.id,
                    'picking_id': package.picking_id.id,
                    'move_id': move_line.move_id.id,
                    'product_id': package.product_id.id,
                    'result_package_id': package.id,
                    'location_id': package.picking_id.picking_type_id.default_location_src_id.id,
                    'location_dest_id': package.picking_id.picking_type_id.default_location_dest_id.id,
                    'quantity': 1,
                    'quantity_product_uom': 1,
                    'is_removeable': False,
                    'state': 'assigned',
                    'picked': True,
                })
        
        return move_line_vals

    def _prepare_batch_picking_vals(self):
        """
        Prepare values for sparepart picking update.
        
        :return: dict of values to write to picking
        """
        picking_vals = {'batch_id': self.id}
        if self.location_id:
            picking_vals['location_dest_id'] = self.location_id.id
        return picking_vals

    def _mark_sparepart_lines_removeable(self, package_obj):
        """Mark sparepart move lines with not assigned to any package as removeable."""
        picking_ids = package_obj.mapped('picking_id')
        removeable_move_lines = self.env['stock.move.line'].suspend_security().search([
            ('result_package_id', 'not in', package_obj.ids),
            ('picking_id', 'in', picking_ids.ids),
            ('move_id.division', '=', 'Sparepart')
        ])
        if removeable_move_lines:
            removeable_move_lines.sudo().write({'is_removeable': True})

    def _process_confirm_unit_lines(self, unit_lines):
        """
        Process unit lines in the batch.
        
        For each line:
        1. Find picking by ship_list_number
        2. Find move by product
        3. Create move line if not exists
        4. Link picking to batch
        
        :param unit_lines: recordset of tw.stock.picking.batch.line with lot_id and no move_id
        :return: list of processed picking ids
        """
        picking_ids = []
        
        for line in unit_lines:
            # Find pickings for this line
            if not hasattr(self, '_find_pickings_for_unit_line'):
                raise Warning("Module tw_b2b_file_stock harus diinstall untuk proses Unit MD!")
            
            move = line.move_id
            self._create_unit_move_line_if_needed(line)
            self._link_picking_to_batch(move.picking_id)
            picking_ids.append(move.picking_id.id)
        
        return picking_ids

    def _create_unit_move_line_if_needed(self, line):
        """
        Create move line for unit line if not already exists.
        
        :param picking: stock.picking record
        :param move: stock.move record
        :param line: tw.stock.picking.batch.line record
        """
        move = line.move_id
        picking = move.picking_id
        search_domain = [
            ('picking_id', '=', picking.id),
            ('move_id', '=', move.id),
            ('product_id', '=', line.lot_id.product_id.id),
        ]
        # Search using lot
        existing_move_line = self.env['stock.move.line'].suspend_security().search(search_domain+[('lot_id', '=', line.lot_id.id)], limit=1)
        
        if not existing_move_line:
            # re-search without lot
            existing_move_line = self.env['stock.move.line'].suspend_security().search(search_domain+[('lot_id', '=', False)], limit=1)
            vals = self._prepare_unit_move_line_vals(move, line)
            if existing_move_line:
                existing_move_line.write(vals)
            else:
                self.env['stock.move.line'].suspend_security().create(vals)

    def _prepare_unit_move_line_vals(self, move, line):
        """
        Prepare values for creating unit move line.
        
        :param move: stock.move record
        :param line: tw.stock.picking.batch.line record
        :return: dict of values for move line creation
        """
        picking = move.picking_id
        vals = {
            'picking_id': picking.id,
            'move_id': move.id,
            'product_id': line.lot_id.product_id.id,
            'lot_id': line.lot_id.id,
            'lot_name': line.lot_id.name,
            'company_id': picking.company_id.id,
            'location_id': picking.picking_type_id.default_location_src_id.id,
            'location_dest_id': line.location_dest_id.id,
            'quantity': 1,
            'quantity_product_uom': 1,
            'is_rfs': line.is_rfs,
            'state': 'assigned',
            'picked': True,
        }
        # Check if unit_position_id field exists
        if 'unit_position_id' in line._fields and line.unit_position_id:
            vals['unit_position_id'] = line.unit_position_id.id
        return vals

    def _link_picking_to_batch(self, picking):
        """
        Link picking to this batch and set stock inbound.
        
        :param picking: stock.picking record
        """
        vals = self._prepare_batch_picking_vals()
        picking.suspend_security().write(vals)

    def _process_confirm_move_lines(self, move_lines):
        """
        Process move lines in the batch.
        
        For each line:
        1. Create move line
        2. Validate quantity
        3. Link picking to batch
        
        :param move_lines: recordset of tw.stock.picking.batch.line with move_id
        """
        for line in move_lines:
            # Step 1: Create move line
            self._create_move_line_from_batch_line(line)
            
            # Step 2: Validate quantity
            self._validate_move_quantity(line)
            
            # Step 3: Link picking to batch
            if not line.move_id.picking_id.batch_id:
                vals = self._prepare_batch_picking_vals()
                line.move_id.picking_id.suspend_security().write(vals)

    def _create_move_line_from_batch_line(self, line):
        """
        Create move line from batch line.
        
        :param line: tw.stock.picking.batch.line record
        """
        vals = self._prepare_batch_move_line_vals(line)
        self.env['stock.move.line'].suspend_security().create(vals)

    def _prepare_batch_move_line_vals(self, line):
        """
        Prepare values for creating move line from batch line.
        
        :param line: tw.stock.picking.batch.line record
        :return: dict of values for move line creation
        """
        vals = {
            'picking_id': line.move_id.picking_id.id,
            'move_id': line.move_id.id,
            'product_id': line.product_id.id,
            'company_id': line.move_id.picking_id.company_id.id,
            'location_id': line.location_id.id,
            'location_dest_id': line.location_dest_id.id if line.location_dest_id else line.move_id.picking_id.picking_type_id.default_location_dest_id.id,
            'quantity': line.quantity,
            'quantity_product_uom': line.quantity,
            'is_rfs': line.is_rfs,
            'state': 'assigned',
            'picked': True,
        }
        if line.lot_id:
            vals.update({
                'lot_id': line.lot_id.id,
                'lot_name': line.lot_id.name,
            })
        if line.lot_name:
            vals.update({
                'lot_name': line.lot_name,
            })
        if line.chassis_number:
            vals.update({
                'chassis_number': line.chassis_number,
            })
        if line.production_year:
            vals.update({
                'production_year': line.production_year,
            })
            
        return vals

    def _cleanup_removeable_all_move_lines(self):
        """
        Remove move lines marked as removeable.
        """
        pickings = self.picking_ids | self.source_picking_ids | self.batch_line_ids.mapped('move_id.picking_id')
        removeable_lines = self.env['stock.move.line'].suspend_security().search([
            ('picking_id', 'in', pickings.ids),
            ('is_removeable', '=', True)
        ])

        if removeable_lines:
            removeable_lines.suspend_security().unlink()

    def _validate_move_quantity(self, line):
        """
        Validate that move line quantity doesn't exceed move quantity.
        
        :param line: tw.stock.picking.batch.line record
        :raises Warning: if quantity exceeds move quantity
        """
        total_qty = sum(line.move_id.move_line_ids.mapped('quantity'))
        if line.move_id.product_uom_qty < total_qty:
            raise Warning(
                f"Quantity move line {total_qty} pada product {line.product_id.default_code} "
                f"tidak boleh lebih besar dari quantity move {line.move_id.product_uom_qty}"
            )

    def _remove_move_line(self, move_obj):
        """
        Remove move lines without lot_id.
        
        Also ensures move quantity matches product_uom_qty before removal.
        
        :param move_obj: stock.move record
        """
        if move_obj.quantity != move_obj.product_uom_qty:
            move_obj.quantity = move_obj.product_uom_qty
            
        move_lines_to_remove = self.env['stock.move.line'].suspend_security().search([
            ('picking_id', '=', move_obj.picking_id.id),
            ('lot_id', '=', False),
            ('lot_name', '=', False),
        ])
        
        if move_lines_to_remove:
            move_lines_to_remove.write({'is_removeable': True})
            move_lines_to_remove.unlink()
