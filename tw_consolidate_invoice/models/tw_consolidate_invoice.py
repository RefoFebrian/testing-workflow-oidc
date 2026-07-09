from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class TWConsolidateInvoice(models.Model):
    _name = "tw.consolidate.invoice"
    _description = "Consolidate Invoice"
    
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False  

    def _get_default_supplier(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].default_supplier_id.id
        return False  

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, default='New')
    date = fields.Date(string='Date', default=fields.Date.today)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], string='Status', default='draft')

    # Audit Trail
    confirm_date = fields.Datetime(string='Confirm Date')
    confirm_uid = fields.Many2one('res.users', string='Confirm User')
    picking_domain = fields.Binary(compute='_compute_picking_domain', store=False, readonly=True, default=lambda self: [('id', '=', 0)])
    
    
    company_id = fields.Many2one('res.company', string='Branch', default=_get_default_branch)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    partner_id = fields.Many2one('res.partner', string='Supplier', default=_get_default_supplier)
    invoice_ids = fields.Many2many('account.move', string='Supplier Invoice')
    purchase_order_ids = fields.Many2many('purchase.order', string='Purchase Orders')
    picking_ids = fields.Many2many('stock.picking', string='Receipt')
    line_ids = fields.One2many('tw.consolidate.invoice.line', 'consolidate_id', string='Consolidate Lines')

    
    # 11: compute/depends & on change methods
    @api.depends('company_id','purchase_order_ids')
    def _compute_picking_domain(self):
        for record in self:
            domain = [('id','=',0)]
            if record.company_id and record.purchase_order_ids:
                picking_ids = self.env['stock.move'].sudo().search([
                    ('company_id', '=', record.company_id.id),
                    ('purchase_line_id.order_id', 'in', record.purchase_order_ids.ids),
                    ('picking_id.state', '=', 'stored')
                    ]).filtered(lambda x: x.consolidated_qty != x.quantity).mapped('picking_id')
                domain = [('id', 'in', picking_ids.ids)]
            record.picking_domain = domain
    
    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.partner_id = self.company_id.default_supplier_id
        self.invoice_ids = False
        self.picking_ids = False

    @api.onchange('division')
    def _onchange_division(self):
        self.invoice_ids = False
        self.picking_ids = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.invoice_ids = False
        self.picking_ids = False

    @api.onchange('purchase_order_ids')
    def _onchange_purchase_order_ids(self):
        pass

    @api.onchange('picking_domain')
    def _onchange_picking_domain(self):
        if self.picking_ids:
            for picking in self.picking_ids:
                # Mengambil ID picking dari fiield domain
                picking_id_domain = self.picking_domain[0][2]
                # Mengambil index 0 dari ids, karena picking.id masih berbentuk <NewId origin=1648>
                picking_id = picking.ids[0]
                # Jika ID picking tidak ada di domain, maka hapus picking dari list
                if picking_id not in picking_id_domain:
                    self.picking_ids -= picking
                    
    @api.onchange('invoice_ids')
    def _onchange_invoice_ids(self):
        # Auto-fill purchase_order_ids from invoice lines
        if self.invoice_ids:
            purchase_orders = self.invoice_ids.mapped('invoice_line_ids.purchase_order_id')
            self.purchase_order_ids = purchase_orders
        else:
            self.purchase_order_ids = False
            self.picking_ids = False
        # Clear picking_ids when invoices change (user needs to re-select)
        return self.sync_line_ids()

    @api.onchange('picking_ids')
    def _onchange_picking_ids(self):
        return self.sync_line_ids()

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            branch_id = vals.get('company_id')
            if not branch_id:
                raise Warning("Branch is required")
            branch_obj = self.env['res.company'].browse(branch_id)
            seq_name = self.env['ir.sequence'].with_company(branch_obj).get_sequence_code('CI', branch_obj.code)
            vals['name'] = seq_name
        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning("Perhatian !\nConsolidate Invoice sudah diproses, data tidak bisa didelete !")
        return super().unlink()

    
    # 13 : action methods
    def action_confirm(self):
        for record in self:
            if record.state == 'done':
                raise Warning("Perhatian !\nConsolidate Invoice sudah diproses !")
            for line in record.line_ids:
                if line.invoice_line_id:
                    line.invoice_line_id.write({'consolidated_qty': line.invoice_line_id.consolidated_qty + line.qty})
                    po_line = line.invoice_line_id.purchase_line_id
                    line.invoice_line_id.purchase_line_id.write({
                        'consolidated_qty': po_line.consolidated_qty + line.qty,
                        'price_unit': line.invoice_line_id.price_unit,
                    })
                    if line.invoice_line_id.consolidated_qty > line.invoice_line_id.quantity:
                        raise Warning("Perhatian !\nConsolidate Invoice sudah melebihi jumlah invoice !")
                if line.stock_move_id:
                    line.stock_move_id.consolidated_qty += line.qty
                    if line.stock_move_id.consolidated_qty > line.stock_move_id.quantity:
                        raise Warning("Perhatian !\nConsolidate Invoice sudah melebihi jumlah picking !")

            # Validate pickings one by one with fresh state checks
            # This prevents errors when moves are shared across pickings (same product in multiple lines)
            for picking in record.picking_ids:
                # Refresh the picking record to get the latest state
                picking.invalidate_recordset(['state', 'is_consolidated'])
                if picking.state == 'stored' and picking.is_consolidated:
                    picking.action_validate_stored_picking()
            
            record.update_serial_number()
            record.write({
                'state': 'done',
                'confirm_date': fields.Datetime.now(),
                'confirm_uid': self.env.user.id,
            })

    # 14: private methods
    def update_serial_number(self):
        for record in self:
            for line in record.line_ids:
                if line.lot_ids:
                    line.lot_ids.write({
                        'supplier_invoice_id': line.invoice_line_id.move_id.id,
                        'supplier_invoice_number': line.invoice_line_id.move_id.supplier_invoice_number,
                    })
                
    def sync_line_ids(self):
        """
        Auto-create consolidate.invoice.line from combination of invoice line and picking line.
        Logic:
        - Loop through each Purchase Order in purchase_order_ids
        - Get invoice lines for this PO that consolidated_qty != quantity
        - Get picking lines for this PO that consolidated_qty != quantity
        - For matching product between invoice line and picking line, create the consolidate line
          (if line with same PO and Product already exists, just update)
        - Remove all other consolidate lines not included from this logic
        """
        for record in self:
            valid_line_keys = set()  # Store (purchase_order_id, product_id) tuples for lines to keep
            
            # Loop through each Purchase Order
            for po in record.purchase_order_ids:
                # Get all invoice lines for this PO that are not fully consolidated
                unconsolidated_invoice_lines = record.invoice_ids.mapped('invoice_line_ids').filtered(
                    lambda l: l.purchase_order_id.id in po.ids
                    and l.consolidated_qty != l.quantity
                    and l.product_id
                )
                
                # Get all picking lines (stock.move) for this PO that are not fully consolidated
                unconsolidated_picking_lines = record.picking_ids.mapped('move_ids').filtered(
                    lambda m: m.purchase_line_id.order_id.id in po.ids
                    and m.consolidated_qty != m.quantity
                    and m.product_id
                )
                
                # Track remaining quantity for each move within this session
                move_remaining_qty = {m.id: m.quantity - m.consolidated_qty for m in unconsolidated_picking_lines}
                
                # Get products present in both invoice lines and picking lines
                invoice_products = unconsolidated_invoice_lines.mapped('product_id')
                picking_products = unconsolidated_picking_lines.mapped('product_id')
                matching_products = invoice_products & picking_products
                
                for product in matching_products:
                    # Get the matching invoice lines for this product
                    inv_lines = unconsolidated_invoice_lines.filtered(lambda l: l.product_id == product)
                    
                    # Get the matching picking lines for this product
                    pick_lines = unconsolidated_picking_lines.filtered(lambda m: m.product_id == product)
                    
                    if inv_lines and pick_lines:
                        for inv_line in inv_lines:
                            unconsolidated_invoice_qty = inv_line.quantity - inv_line.consolidated_qty
                            for pick_line in pick_lines:
                                if unconsolidated_invoice_qty <= 0:
                                    break

                                unconsolidated_move_qty = move_remaining_qty.get(pick_line.id, 0)
                                if unconsolidated_move_qty <= 0:
                                    continue

                                line_key = (inv_line.id, pick_line.id)
                                valid_line_keys.add(line_key)

                                # Check if line with same inv_line and pick_line already exists
                                existing_line = record.line_ids.filtered(
                                    lambda l: l.invoice_line_id.id == inv_line.id 
                                    and l.stock_move_id.id == pick_line.id
                                )
                        
                                to_consolidate_qty = min(unconsolidated_invoice_qty, unconsolidated_move_qty)
                                unconsolidated_invoice_qty -= to_consolidate_qty
                                move_remaining_qty[pick_line.id] -= to_consolidate_qty
                                
                                
                                # Prepare values
                                line_vals = {
                                    'qty': to_consolidate_qty,
                                    'invoice_qty': unconsolidated_invoice_qty,
                                    'move_qty': unconsolidated_move_qty,
                                    'unit_price': inv_line.price_unit,
                                    'untaxed_price': inv_line.price_subtotal / inv_line.quantity if inv_line.quantity > 0 else 0,
                                    'purchase_order_id': po.id,
                                    'product_id': product.id,
                                    'invoice_line_id': inv_line.id,
                                    'stock_move_id': pick_line.id,
                                }
                                
                                # Add lot_id if available from picking line
                                if pick_line.lot_ids:
                                    line_vals['lot_ids'] = [(6, 0, pick_line.lot_ids.ids)]
                                
                                if existing_line:
                                    # Update existing line
                                    existing_line.write(line_vals)
                                else:
                                    # Create new line
                                    line_vals['consolidate_id'] = record.id
                                    record.line_ids = [(0, 0, line_vals)]
            
            # Remove lines that are not in valid_line_keys
            lines_to_remove = record.line_ids.filtered(
                lambda l: (l.invoice_line_id.id, l.stock_move_id.id) not in valid_line_keys
            )
            if lines_to_remove:
                record.line_ids = [(3, line.id) for line in lines_to_remove]