# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, Command, _
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockPicking(models.Model):
    _inherit = "stock.picking"
    
    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()

    # 8: fields
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    start_date = fields.Date(string='Start Date', help='Tanggal Mulai Aktual')
    end_date = fields.Date(string='End Date', help='Tanggal Akhir Aktual')
    min_date = fields.Datetime(string='Min Date', help='Tanggal Minimal Aktual')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    branch_type = fields.Char(related='company_id.branch_type_id.value', string='Branch Type', readonly=True)
    partner_category_name = fields.Char(compute='_compute_partner_category', string='Partner Category Name')
    backorder_count = fields.Integer(string="Backorder Count",compute="_compute_backorder")
    type = fields.Selection([('regular', 'Regular'), ('mutation', 'Mutation'), ('internal', 'Internal Transfer')], default='regular')
    is_include_sublocations = fields.Boolean(string="Include Sublocations?", help="Show all stock from the location and its sublocations")
    
    # Audit Trail
    validate_date = fields.Datetime(string='Validate Date', help='Tanggal Validasi')
    validate_uid = fields.Many2one(comodel_name='res.users', string='Validate User', help='User yang melakukan validasi')
    
    is_returnable_step = fields.Boolean(string="Is Returnable Step", compute="_compute_is_returnable_step", help="Shows True if there are no further active destination moves.")
    
    # 9: relation fields
    move_ids_without_package = fields.One2many('stock.move', 'picking_id')
    move_ids_without_extras = fields.One2many(
        'stock.move',
        'picking_id',
        string='Operation',
        domain=[('division', '!=', 'Extras')],
    )
    company_id = fields.Many2one('res.company', 'Branch', required=True, index=True, copy=True)
    partner_id = fields.Many2one('res.partner', 'Partner',check_company=False, index='btree_not_null')
    all_backorder_ids = fields.Many2many('stock.picking', compute='_compute_backorder',string="All Backorders",store=False)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('origin', 'name')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            if record.origin:
                name = f"{record.origin} - {name} "
            if getattr(record, 'mft_reference', False):
                name = f"[{record.mft_reference}] {name}"
            record.display_name = name

    @api.depends('partner_id')
    def _compute_partner_category(self):
        for record in self:
            record.partner_category_name = False
            if record.partner_id:
                partner_category = [categ.name for categ in record.partner_id.category_id]
                if 'Customer' in partner_category:
                    record.partner_category_name = 'Customer'
                else:
                    record.partner_category_name = 'Non Customer'

    @api.depends('backorder_ids')
    def _compute_backorder(self):
        for rec in self:
            rec.all_backorder_ids = rec._get_all_backorders()
            rec.backorder_count = len(rec.all_backorder_ids)
            
    @api.depends('state', 'move_ids', 'move_ids.move_dest_ids.state')
    def _compute_is_returnable_step(self):
        for picking in self:
            if picking.state != 'done':
                picking.is_returnable_step = False
                continue
            
            is_returnable = True
            for move in picking.move_ids:
                if move.move_dest_ids.filtered(lambda m: m.state != 'cancel'):
                    # There are subsequent active moves, not the end of the chain
                    is_returnable = False
                    break
                    
            picking.is_returnable_step = is_returnable

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if not vals.get('company_id') and vals.get('picking_type_id'):
                vals['company_id'] = self.env['stock.picking.type'].browse(vals['picking_type_id']).company_id.id
            # Give sequence name
            company_id = vals.get('company_id', self.default_get(['company_id']).get('company_id'))
            company_obj = self.env['res.company'].browse(company_id)
        picking_objs =  super(InheritStockPicking, self).create(vals_list)
        
        if 'import_file' in self._context and self._context.get('import_file'):
            picking_objs._process_assign_purchase_order_line_picking()
            
        return picking_objs
    
    def write(self,vals):
        return super(InheritStockPicking, self).write(vals)
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning(_("Picking can not be removed unless the state is draft!"))
            
        return super().unlink()
    
    def name_get(self):
        if self._context is None:
            self._context = {}
        res = []
        for record in self:
            tit = "%s" % (record.name)
            if record.origin:
                tit = f"[{record.origin}] {record.name}"
            if getattr(record, 'mft_reference', False):
                tit = f"[{record.mft_reference}] {tit}"
            res.append((record.id, tit))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|', ('name', operator, name), ('origin', operator, name)] + args
            if 'mft_reference' in self._fields:
                args = ['|', ('mft_reference', operator, name)] + args
        categories = self.search(args, limit=limit)
        return categories.name_get()
    
    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_stock.group_tw_stock_picking_form_read'):
            raise Warning(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
    
    def _can_return(self):
        """
        Override to enforce end-of-chain return logic.
        A picking can only be returned if it is at the end of the picking chain 
        (i.e., all its moves have no further destination moves that are not cancelled).
        """
        res = super()._can_return()
        if not res:
            return False
        # Check if all moves in this picking are the last in the chain
        for move in self.move_ids:
            if move.move_dest_ids.filtered(lambda m: m.state != 'cancel'):
                # There are subsequent moves, so this is NOT the end of the chain
                return False
        return True
    
    # 13: action methods
    def action_confirm(self):
        res = super(InheritStockPicking, self).action_confirm()
        for picking in self:
            picking._process_confirm_picking()
        return res
    
    def button_validate(self):
        self._check_valid_picking()
        to_validate_picking = self.with_company(self.company_id)
        to_validate_picking._create_auto_batch()
        res = super(InheritStockPicking, to_validate_picking).button_validate()
        for picking in to_validate_picking:
            picking._process_validate_picking()
        return res
    
    def action_print_travel_document(self):
        self.ensure_one()
        return self.env.ref('tw_stock.travel_document_stock_picking_report').report_action(self.id)

    def action_print_picking_list(self):
        self.ensure_one()
        return self.env.ref('tw_stock.picking_list_stock_picking_report').report_action(self.id)
    
    def action_renew_available(self):
        if self.move_ids_without_package:
            for move in self.move_ids_without_package:
                qty_available = self.env['stock.quant'].get_stock_available(move.product_id.id, self.company_id.id, False, move.location_id.id)
                move.qty_available = qty_available

    def action_detailed_operations(self):
        action = super().action_detailed_operations()
        action['context']['create'] = False
        action['context']['edit'] = False
        return action

    def action_update_validate(self):
        return self.suspend_security().write({
            'validate_date': self.get_default_datetime(),
            'validate_uid': self.env.user.id,
        })

    def action_view_backorders(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').sudo().read()[0]
        action['domain'] = [('id', 'in', self.all_backorder_ids.ids)]

        action['views'] = [
            (self.env.ref('stock.vpicktree').id, 'list'),
            (self.env.ref('stock.view_picking_form').id, 'form'),
        ]

        return action

    
    def action_view_batch(self):
        self.ensure_one()
        form_view_id = self.env.ref('tw_stock.tw_stock_picking_batch_original_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking.batch',
            'res_id': self.batch_id.id,
            'view_mode': 'form',
            'views': [(form_view_id, 'form')],
            'context': {
                'default_division': self.division,
                'sequence_code': self.picking_type_id.sequence_code,
            }
        }

    # 14: private methods
    def _check_valid_picking(self):
        # Ensure the company used is the transaction company
        if len(self.company_id) > 1:
            raise Warning(_("All selected pickings must belong to the same company. Please select only one company from the list."))

        for picking in self:
            picking.validate_duplicate_serial_number()
            for move in picking.move_ids:
                if move.quantity < 0:
                    raise Warning(_("Perhatian! Quantity tidak boleh negatif!\nProduk: %(product)s\nQuantity: %(quantity)s", product=move.product_id.name, quantity=move.quantity))
                
                if move.quantity == 0:
                    continue
                
                # Default tracking ('serial', 'lot') atau custom tracking ('serial_chassis')
                is_tracked = False
                if hasattr(move, 'has_chassis_tracking') and move.has_chassis_tracking in ('serial', 'serial_chassis'):
                    is_tracked = True
                elif move.product_id.tracking in ('serial', 'lot'):
                    is_tracked = True

                if is_tracked:
                    if not move.move_line_ids:
                        raise Warning(_("Permintaan Validasi Ditolak!\nProduk '%s' memerlukan input Serial Number / Lot, namun belum ditentukan.", move.product_id.display_name))
                    for line in move.move_line_ids:
                        if not line.lot_id and not line.lot_name:
                            raise Warning(_("Permintaan Validasi Ditolak!\nProduk '%s' memerlukan input Serial Number / Lot, namun ditemukan baris yang kosong.", move.product_id.display_name))

    
    def validate_duplicate_serial_number(self):
        """Validate duplicate serial number on move_line_ids."""
        if not self.move_ids_without_package or not self.move_line_ids:
            return

        seen_chassis = []
        seen_names = {}
        for move in self.move_ids_without_package:
            for line in move.move_line_ids:
                # Resolve the effective serial name from whichever input mode is active
                serial_name = None
                if line.lot_id:
                    serial_name = line.lot_id.name
                elif line.lot_name:
                    serial_name = line.lot_name

                if not serial_name:
                    continue

                if serial_name in seen_names:
                    raise Warning(_(
                                "Gagal Validate : Unit dengan serial number '%(serial)s' sudah di input.\n"
                                "Mohon pilih serial number lain untuk produk '%(product)s'.",
                                serial=serial_name,
                                product=move.product_id.name,
                            ))
                seen_names[serial_name] = True

                # Check also the chassis
                if line.chassis_number:
                    if line.chassis_number in seen_chassis:
                        raise Warning("Unit dengan chassis number '%s' sudah di input.\nMohon pilih chassis number lain."%line.chassis_number)
                    seen_chassis.append(line.chassis_number)
        
    def _is_main_dealer(self):
        try:
            md_code = self.env['res.company'].get_default_main_dealer_code()
        except:
            # Jika settingan sistem tidak memiliki Main Dealer, maka perlakukan seperti dealer biasa.
            return False

        if self.company_id.code == md_code and self.company_id.branch_type_id.value == 'MD':
            return True

        return False
        
    def _is_incoming_md(self):
        is_main_dealer = self._is_main_dealer()
        if not is_main_dealer:
            return False
        
        ahm_code = self.env['res.company'].get_default_main_dealer().default_supplier_id.code
        picking_type_incoming = self._get_picking_type_incoming(self.company_id)
        if is_main_dealer and self.partner_id.code == ahm_code and (self.picking_type_id.id in picking_type_incoming or self.picking_type_id.code == 'incoming'):
            return True
        
        return False

    def _process_confirm_picking(self):
        self.ensure_one()
        for move in self.move_ids_without_package:
            self._process_confirm_move(move)
    
    def _process_confirm_move(self, move):
        self.ensure_one()
        move._check_valid_qty()

    def _process_validate_picking(self):
        self.ensure_one()
        for move in self.move_ids:
            self._process_validate_move(move)
        self.handle_backorder_sparepart_include_package()
        self.action_update_validate()

    def _process_validate_move(self, move):
        self.ensure_one()
        move._check_valid_qty()
        for move_line in move.move_line_ids:
            self._process_validate_move_line(move, move_line)

    def _process_validate_move_line(self, move, move_line):
        self.ensure_one()
        requires_lot_update = False
        is_last_move = move._is_last_move_from_route()
        picking_type_incoming = self._get_picking_type_incoming(move.picking_id.company_id)
        picking_type_outgoing = self._get_picking_type_outgoing(move.picking_id.company_id)
        if is_last_move and (move.picking_id.picking_type_id.id in picking_type_incoming or move.picking_id.picking_type_id.code == 'incoming'):
            requires_lot_update = True
            is_incoming_md = move.picking_id._is_incoming_md()
            if is_incoming_md:
                self._update_quant(move_line)
            
        elif is_last_move and (move.picking_id.picking_type_id.id in picking_type_outgoing or move.picking_id.picking_type_id.code == 'outgoing'):
            requires_lot_update = True
            # Pada saat pengeluaran MD, remove reservation pada quant
            is_main_dealer = move.picking_id._is_main_dealer()
            if is_main_dealer:
                quant_obj = self.env['stock.quant'].search([
                    ('lot_id', '=', move_line.lot_id.id),
                    ('quantity', '=', move_line.quantity),
                    ('reservation_ids', 'in', [move_line.move_id.id] if move_line.move_id else [])
                ], limit=1)
                if quant_obj and quant_obj.reservation_ids:
                    # Use (3, id, 0) to remove the relation without deleting the move
                    quant_obj.suspend_security().write({
                        'reservation_ids': [(3, move_line.move_id.id, 0)]
                    })
        
        if requires_lot_update:
            self._update_lot(move.picking_id, move, move_line)

        if move_line.result_package_id:
            picking_next_transfer_obj = self._get_next_transfers()
            if picking_next_transfer_obj:
                move_line.result_package_id.write({'picking_id': picking_next_transfer_obj[0].id})
                
            # KHUSUS step penerimaan truk (First Step / Incoming) baru kurangi saldonya:
            if self.picking_type_id.code == 'incoming' and self._is_incoming_md():
                # Pada saat penerimaan MD, update sisa qty pada package berdasarkan nomor kardus
                if move_line.result_package_id.current_quantity >= move_line.quantity:
                    current_quantity = move_line.result_package_id.current_quantity - move_line.quantity
                    if current_quantity < 0:
                        raise Warning(f"Current quantity on package {move_line.result_package_id.name} is {current_quantity} less than quantity move line {move_line.quantity}")
                    move_line.result_package_id.write({'current_quantity': current_quantity})

    def _get_picking_type(self,company_id):
        picking_type_ids = self.env['stock.picking.type'].search([('company_id','=',company_id),('code','in',['outgoing','interbranch_out'])])
        if not picking_type_ids:
            return False
        return picking_type_ids

    def _get_picking_type_incoming(self, company_id):
        picking_type_incoming = self.env['stock.picking.type'].suspend_security().search([
            ('company_id', '=', company_id.id),
            ('sequence_code', 'in', ['IN', 'QC', 'STOR'])
        ])
        return picking_type_incoming.ids if picking_type_incoming else []

    def _get_picking_type_outgoing(self, company_id):
        picking_type_outgoing = self.env['stock.picking.type'].suspend_security().search([
            ('company_id', '=', company_id.id),
            ('sequence_code', 'in', ['PICK', 'PACK', 'OUT'])
        ])
        return picking_type_outgoing.ids if picking_type_outgoing else []

    def _get_qty_picking(self,company_id=False,division=False,product_id=False):
        company_id = company_id
        if type(company_id) != int:
            company_id = company_id.id
        if not division:
            raise Warning('Tidak ada Division untuk cek Qty Picking')
        if not product_id:
            raise Warning('Tidak ada Product untuk cek Qty Picking')
        qty_picking_product = 0
        domain = [('division','=',division),
                ('state','not in',('draft','cancel','done'))]
        if company_id:
            domain = expression.AND([[('company_id', '=', company_id)], domain])
        picking_type = self._get_picking_type(company_id)
        if picking_type:
            domain = expression.AND([[('picking_type_id','in',picking_type.ids),], domain])
            picking_ids = self.search(domain)
            if picking_ids:
                move_ids = self.env['stock.move'].suspend_security().search([('picking_id','in',picking_ids.ids),('product_id','=',product_id)])
                if move_ids:
                    for move in move_ids:
                        qty_picking_product+=move.product_uom_qty
        return qty_picking_product

    def _get_location(self,company_id):
        location_ids = False
        if company_id:
            location_ids = self.env['stock.location'].search(['|',('company_id','=',company_id),('company_id','=',company_id),('usage','=','internal')])
        if not location_ids:
            return False
        return location_ids.ids
    
    def _get_qty_quant(self,company_id,product_id):
        raise Warning('This method is depreciated, for checking stock, please use get_stock_available() on stock.quant instead.')
    
    def _get_qty_rfa_approved(self, company_id, division, product_id, location_id):
        # TODO : Activated This Query MO when MO done Migrate
        query = f"""
            SELECT 
                SUM(qty) 
            FROM (
                SELECT 
                    COALESCE(SUM(sol.product_uom_qty),0) AS qty
                FROM tw_sale_order_line sol
                JOIN tw_sale_order so ON sol.order_id = so.id
                WHERE so.company_id = {company_id}
                AND so.division = '{division}'
                AND so.state IN ('waiting_for_approval','approved')
                AND sol.product_id = {product_id}
                AND so.location_id = {location_id}
                -- UNION ALL
                -- SELECT
                --    COALESCE(SUM(tmol.qty), 0) AS qty
                -- FROM tw_mutation_order tmo 
                -- JOIN tw_mutation_order_line tmol ON tmol.mutation_order_id = tmo.id
                -- WHERE tmo.company_id = {company_id}
                -- AND tmo.division = '{division}'
                -- AND tmo.state in ('waiting_for_approval','approved')
                -- AND tmol.product_id = {product_id}
                -- AND tmo.location_id = {location_id}
            ) AS so_mo
        """
        self._cr.execute(query)
        return self._cr.fetchone()[0]
    
    def _get_file_travel_document(self):
        self.ensure_one()
        report_obj = self.env['ir.actions.report'].suspend_security()
        pdf_content, content_type = report_obj._render(
            report_ref='tw_stock.travel_document_stock_picking_report',
            res_ids=[self.id]
        )

        return base64.b64encode(pdf_content).decode('utf-8')
    
    def _prepare_update_lot(self, picking, move=False, move_line=False):
        vals = {
            'company_id':picking.company_id.id,
            'ready_for_sale': 'good' if move_line.is_rfs else 'not_good'
        }
        if move_line.lot_id.location_id.id != move_line.location_dest_id.id:
            vals.update({'location_id': move_line.location_dest_id.id})

        is_incoming_md = picking._is_incoming_md()
        if is_incoming_md:
            vals.update({'receive_date':self.get_default_datetime()})
        return vals
        
    def _update_lot(self, picking, move, move_line):
        if move_line.lot_id:
            vals = self._prepare_update_lot(picking,move,move_line)
            if move_line.lot_id.state == 'intransit':
                vals.update({'state':'stock'})
            # Revert lot status saat Return dari Sale Order (WHO → Customer → Return)
            if move.origin_returned_move_id and move_line.lot_id.state in ('sold', 'sold_offtr','paid','paid_offtr','reserved'):
                vals.update({
                    'state': 'stock',
                    'partner_id': False,
                })
            if picking.batch_id:
                vals.update({'batch_transfer_id': picking.batch_id.id})
            move_line.lot_id.suspend_security().write(vals)
            
    def _update_quant(self, move_line):
        quant_obj = self.env['stock.quant'].search([
            ('product_id','=',move_line.product_id.id),
            ('quantity','=',move_line.quantity),
            ('location_id','=',move_line.location_dest_id.id),
            ('consolidated_date','=',False)
        ])
        for quant in quant_obj:
            vals = {'consolidated_date': self.get_default_datetime()}
            if move_line.lot_id and not quant.lot_id:
                vals.update({'lot_id': move_line.lot_id.id})
            quant.write(vals)
            
    def _get_ids_picking(self, origin):
        """
        To get picking ids from origin
        """
        if not origin and type(origin) != str:
            raise Warning("Origin is not set")
        ids_picking = self.search([
            ('origin','=', origin),
            ('state', '!=', 'cancel')
        ])
        return ids_picking
    
    def _get_all_backorders(self):
        """Ambil semua backorder (langsung & tidak langsung) secara rekursif."""
        collected_ids = set()

        def recurse(picking):
            for backorder in picking.backorder_ids:
                if backorder.id not in collected_ids:
                    collected_ids.add(backorder.id)
                    recurse(backorder)

        recurse(self)
        return self.env['stock.picking'].browse(list(collected_ids))

    def handle_backorder_sparepart_include_package(self):
        """
            Pada penerimaan sparepart MD dari AHM, jika membentuk backorder,
            maka assign juga package nya sesuai dengan jumlah sisa quantity.
        """
        if self._is_main_dealer():
            backorder_obj = self.env['stock.picking'].suspend_security().search([
                ('backorder_id', '=', self.id),
                ('company_id.code', '=', self.env['res.company'].get_default_main_dealer_code()),
                ('partner_id.code', '=', self.env['res.company'].get_default_main_dealer().default_supplier_id.code),
                ('division', '=', 'Sparepart'),
                ('state', 'not in', ['cancel', 'done'])
            ], limit=1)
            if backorder_obj:
                move_line_removeable = backorder_obj.move_line_ids.filtered(lambda x: x.is_removeable)
                if move_line_removeable:
                    move_line_removeable.sudo().unlink()

                for move in backorder_obj.move_ids_without_package:
                    package_obj = self.env['stock.quant.package'].suspend_security().search([
                        ('picking_id', '=', self.id),
                        ('product_id', '=', move.product_id.id),
                        ('current_quantity', '>', 0),
                    ])
                    if package_obj:
                        for package in package_obj:
                            move_line = {
                                'picking_id': backorder_obj.id,
                                'move_id': move.id,
                                'product_id': move.product_id.id,
                                'company_id': move.company_id.id,
                                'location_id': move.location_id.id,
                                'location_dest_id': move.location_dest_id.id,
                                'result_package_id': package.id if package.current_quantity == package.quantity else False,
                                'is_removeable': False,
                                'quantity': 0,
                                'quantity_product_uom': 0
                            }
                            self.env['stock.move.line'].sudo().create(move_line)
                            package.sudo().write({'picking_id': backorder_obj.id})
                        
    def _create_auto_batch(self):
        for picking in self:
            if not picking.picking_type_id.auto_batch or picking.batch_id or not picking.move_ids:
                continue
            
            new_batch_data = {
                'picking_ids': [Command.link(picking.id)],
                'source_picking_ids': [Command.link(picking.id)],
                'company_id': picking.company_id.id if picking.company_id else False,
                'picking_type_id': picking.picking_type_id.id,
                'division': picking.division,
                'description': picking._get_auto_batch_description()
            }
            new_batch = self.env['stock.picking.batch'].sudo().create(new_batch_data)
        
    def _find_auto_batch(self):
        """
            Override to prevent auto batch creation.
            Sudah tidak menggunakan auto batch bawaan odoo karena batch terbentuk saat status assign (Confirm Picking),
            sedangkan auto batch hanya dibutuhkan untuk pencatatan/penomoran otomatis jika user tidak melakukan picking lewat batch (Batch dibentuk saat validate Picking tanpa batch). 
            pada skema saat ini batch di create manual, dan hanya create otomatis jika melalui validate picking dengan aturan batchnya belum terbuat.
        """
        self.ensure_one()
        return False
    
    def _process_assign_purchase_order_line_picking(self):
        """
            relasi untuk purchase_order_line dengan stock move pada proses import data (migrasi)
            dan unlink created_purchase_line_ids
        """
        for picking_obj in self:
            for move_obj in picking_obj.move_ids:
                if not move_obj.purchase_line_id and move_obj.created_purchase_line_ids:
                    move_obj.purchase_line_id = move_obj.created_purchase_line_ids[0].id

        return True
