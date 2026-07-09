# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, UserError, ValidationError
from odoo.tools import float_is_zero


class PartSales(models.Model):
    _name = "tw.part.sales"
    _order = "id desc"
    _inherit = "sale.order"
    _description = "TW Part Sales"

    _sql_constraints = [
        ('date_order_conditional_required',
         "CHECK((state = 'sale' AND date_order IS NOT NULL) OR state != 'sale')",
         "A confirmed Part Sales requires a confirmation date."),
    ]

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()
    
    def _get_default_main_dealer_code(self):
        return self.env['res.company'].get_default_main_dealer_code()

    # 8: fields
    chassis_number = fields.Char(string='Nomor Rangka')
    discount_cash = fields.Float('Discount Cash', digits='Product Price')
    discount_cash_percent = fields.Float('Discount Cash (%)', digits='Product Price')
    discount_program = fields.Float('Discount Program', digits='Product Price')
    discount_other = fields.Float('Other Discount', digits='Product Price')
    # Selection
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Open'),
        ('cancel', 'Cancelled'),
        ('done','Done'),
        ('unused','Unused'),
    ], string="Status", readonly=True, copy=False, index=True, tracking=3, default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options_list(['Sparepart','Umum']),default='Sparepart')
    # 9: relation fields
    # Customer
    partner_stnk_id = fields.Many2one(comodel_name='res.partner', string="Customer STNK", domain=[('category_id.name', '=', 'Customer')])
    partner_type = fields.Selection(selection=[
        ('perorangan','Perorangan'),
        ('ahass','AHASS'),
        ('non_ahass','Non AHASS')
    ], string="Type")
    partner_mobile = fields.Char(string='Mobile')
    partner_state_id = fields.Many2one(comodel_name='res.country.state', string="Provinsi")
    partner_city_id = fields.Many2one(comodel_name='res.city', string="Kota/Kabupaten", domain="[('state_id', '=', partner_state_id)]")
    partner_district_id = fields.Many2one(comodel_name='res.district', string="Kecamatan", domain="[('city_id', '=', partner_city_id)]")
    partner_sub_district_id = fields.Many2one(comodel_name='res.sub.district', string="Kelurahan", domain="[('district_id', '=', partner_district_id)]")
    partner_street = fields.Char(string="Alamat")

    lot_id = fields.Many2one('stock.lot', string='Nomor Mesin')
    product_id = fields.Many2one('product.product', string="Product")
    order_line = fields.One2many(comodel_name='tw.part.sales.line',inverse_name='order_id',string="Order Lines")
    transaction_ids = fields.Many2many(comodel_name='payment.transaction',relation='tw_part_sales_tw_transaction_rel', column1='order_id', column2='transaction_id',string="Transactions")
    tag_ids = fields.Many2many(comodel_name='crm.tag',relation='tw_part_sales_tw_tag_rel', column1='order_id', column2='tag_id',string="Tags")

    # Audit Trail
    confirm_uid = fields.Many2one('res.users', 'Confirmed by')
    confirm_date = fields.Datetime('Confirmed on')
    open_uid = fields.Many2one('res.users', 'Open by')
    open_date = fields.Datetime('Open on')
    done_uid = fields.Many2one('res.users', 'Done by')
    done_date = fields.Datetime('Done on')
    cancel_uid = fields.Many2one('res.users', 'Cancelled by')
    cancel_date = fields.Datetime('Cancelled on')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('partner_id')
    def _onchange_part_sales_partner_id(self):
        self.partner_mobile = False
        self.partner_state_id = False
        self.partner_city_id = False
        self.partner_district_id = False
        self.partner_sub_district_id = False
        self.partner_street = False
        self.lot_id = False
        if self.partner_id:
            self.partner_mobile = self.partner_id.mobile
            self.partner_state_id = self.partner_id.state_id
            self.partner_city_id = self.partner_id.city_id
            self.partner_district_id = self.partner_id.district_id
            self.partner_sub_district_id = self.partner_id.sub_district_id
            self.partner_street = self.partner_id.street
    
    @api.onchange('partner_state_id')
    def _onchange_part_sales_partner_state_id(self):
        self.partner_city_id = False
        self.partner_district_id = False
        self.partner_sub_district_id = False

    @api.depends('company_id')
    def onchange_company_id(self):
        self.warehouse_id = False
        if self.company_id:
            warehouse_obj = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], order="id DESC", limit=1)
            if warehouse_obj:
                self.warehouse_id = warehouse_obj.id

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        self.chassis_number = False
        self.product_id
        self.partner_stnk_id = False
        if self.lot_id:
            self.chassis_number = self.lot_id.chassis_number
            self.product_id = self.lot_id.product_id.id
            self.partner_stnk_id = self.lot_id.partner_id.id

    @api.depends('discount_cash_percent')
    def onchange_discount_cash(self):
        if self.discount_cash_percent > 100:
            raise Warning("Attention!, Maximum Discount Cash is 100%")
        
        if self.discount_cash_percent < 0:
            raise Warning("Attention! You cannot Input Negative Values")
        
        
    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:            
            invoices = order.order_line.sudo().invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    @api.depends('state')
    def _compute_type_name(self):
        for record in self:
            if record.state in ('draft', 'sent', 'cancel'):
                record.type_name = _("Quotation")
            else:
                record.type_name = _("Part Sales")

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('company_id'):
                branch_src = self.env['res.company'].suspend_security().search([('id','=',vals['company_id'])],limit=1)
                seq_name = self.env['ir.sequence'].with_company(branch_src).get_sequence_code('PS', branch_src.code)
                vals['name'] = seq_name
        return super(PartSales, self).create(vals_list)
    
    def write(self, vals):
        if 'pricelist_id' in vals and any(so.state == 'sale' for so in self):
            raise UserError(_("You cannot change the pricelist of a confirmed part sales !"))
        res = super().write(vals)
        if vals.get('partner_id'):
            self.filtered(lambda so: so.state in ('sent', 'sale')).message_subscribe(
                partner_ids=[vals['partner_id']],
            )
        return res
    
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a State other than draft!')
            else:
                raise Warning('Warning! \nCannot delete records!')
        return super(PartSales, self).unlink()
    
    def action_confirm(self):
        self._prepare_confirmation()
        return super(PartSales,self.with_context(model_name='tw.part.sales')).action_confirm()

    def _prepare_invoice(self):        
        self.suspend_security().write({
            'journal_id': self.get_branch_journal_config().get('journal_part_sales').id,
        })
        prepare_invoice = super()._prepare_invoice()

        code = self.journal_id.code
        prefix = self.company_id.code
        
        prepare_invoice.update({
            'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
            'company_id': self.company_id.id,
            'ref': self.name,
            'division': self.division,
            'invoice_date': self.date_order
        })

        return prepare_invoice
    
    def _create_invoices(self, grouped=False, final=False, date=None):        
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)        
        # Update Invoice Values, because creating is not use create() method
        for line in moves.line_ids:
            line.company_id = moves.company_id.id
        return moves
    
    
    def action_unused(self):
        self.write({ 'state':'unused' })

    def action_done(self):
        self.write({
            'state':'done',
            'done_uid': self.env.uid,
            'done_date': datetime.now()
        })

    def action_set_amount_invoiced(self):
        total_inv = self.invoice_total()
        if not total_inv:
            total_inv = 0

        self.suspend_security().write({ 'amount_invoiced': total_inv })
    
    def _get_report_base_filename(self):
        self.ensure_one()
        return f'{self.type_name} {self.name}'
    
    def _test_moves_done(self):
        if not self.picking_ids :
            return False
        for picking in self.picking_ids:
            if picking.state != 'done':
                return False
        return True

    def renew_available(self):
        self.order_line.renew_available()
    
    def action_part_sales_report(self):
        self.ensure_one()
        return self.env.ref('tw_part_sales.invoice_part_sales_report').report_action(self.id)
    
    def get_branch_journal_config(self):
        account_setting_id = self.company_id.branch_setting_id.account_setting_id
        if not account_setting_id:
            raise Warning("Attention! The Account Setting is Incomplete. Please Set it up First.")
        
        journal_part_sales = account_setting_id.journal_part_sales_umum_id
        if self.division == 'Sparepart':
            journal_part_sales = account_setting_id.journal_part_sales_sparepart_id

        if not journal_part_sales:
            raise Warning("Attention! The Journal Part Sales is Incomplete. Please Set it up First.")
        
        journal_list = {
            'journal_part_sales': journal_part_sales
        }
        return journal_list
    
    def _action_cancel(self):
        sale_order_cancel = super(PartSales,self)._action_cancel()
        self.write({
            'cancel_uid': self.env.uid,
            'cancel_date': datetime.now()
        })
        return sale_order_cancel
    
    def _generate_downpayment_invoices(self):
        """ Generate invoices as down payments for part sales.

        :return: The generated down payment invoices.
        :rtype: recordset of `account.move`
        """
        generated_invoices = self.env['account.move']        

        for order in self:
            downpayment_wizard = order.env['tw.part.sale.advance.payment.inv'].create({
                'part_sales_ids': order,
                'advance_payment_method': 'fixed',
                'fixed_amount': order.amount_paid,
            })
            generated_invoices |= downpayment_wizard._create_invoices(order)

        return generated_invoices
    
    def action_print_part_sales_thermal(self):
        self.ensure_one()
        return self.env.ref('tw_part_sales.print_part_sales_thermal_action').report_action(self)
    
    def action_print_picking_part_sales_thermal(self):
        self.ensure_one()
        return self.env.ref('tw_part_sales.print_picking_part_sales_thermal_action').report_action(self)

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:            
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['tw.part.sales.line'].browse(invoiceable_line_ids + down_payment_line_ids)
    
    @api.depends('state', 'order_line.invoice_status')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a PS. Possible statuses:
        - no: if the PS is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any PS line is 'to invoice', the whole PS is 'to invoice'
        - invoiced: if all PS lines are invoiced, the PS is invoiced.
        - upselling: if all PS lines are invoiced or upselling, the status is upselling.
        """
        confirmed_orders = self.filtered(lambda ps: ps.state == 'sale')
        (self - confirmed_orders).invoice_status = 'no'
        if not confirmed_orders:
            return
        lines_domain = [('is_downpayment', '=', False), ('display_type', '=', False)]
        line_invoice_status_all = [
            (order.id, invoice_status)
            for order, invoice_status in self.env['tw.part.sales.line']._read_group(
                lines_domain + [('order_id', 'in', confirmed_orders.ids)],
                ['order_id', 'invoice_status']
            )
        ]
        for order in confirmed_orders:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state != 'sale':
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                if any(invoice_status == 'no' for invoice_status in line_invoice_status):
                    # If only discount/delivery/promotion lines can be invoiced, the SO should not
                    # be invoiceable.
                    invoiceable_domain = lines_domain + [('invoice_status', '=', 'to invoice')]
                    invoiceable_lines = order.order_line.filtered_domain(invoiceable_domain)
                    special_lines = invoiceable_lines.filtered(
                        lambda sol: not sol._can_be_invoiced_alone()
                    )
                    if invoiceable_lines == special_lines:
                        order.invoice_status = 'no'
                    else:
                        order.invoice_status = 'to invoice'
                else:
                    order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'
    
    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'state')
    def _compute_qty_to_invoice(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:                        
            if line.state == 'sale' and not line.display_type:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0
    
    def _prepare_confirmation(self):
        self.write({
            'date_order': datetime.now(),
            'confirm_uid': self.env.uid,
            'confirm_date': datetime.now()
        })

        total_qty = 0
        qty = {}
        
        if self.state == 'approved' :
            for sol in self.order_line :
                qty[sol.product_id] = qty.get(sol.product_id,0) + sol.product_uom_qty
        
        for sol in self.order_line:
            self.env['stock.quant'].compare_stock_on_transaction( self.company_id.id, self.division, sol.product_id.id, sol.product_uom_qty, sol.location_id.id )
            total_qty += sol.product_uom_qty

        self.state = 'sent'

    def action_open(self):
        self.suspend_security().action_confirm()
        self.write({
            'state':'sale',
            'open_uid': self.env.uid,
            'open_date': datetime.now()
        })

    def action_create_invoice(self):
        if any(line.qty_delivered == 0 or not line.order_id.picking_ids for line in self.order_line):
            raise ValidationError("Sparepart belum dilakukan picking. Silahkan selesaikan picking terlebih dahulu.")
        invoice = self._create_invoices()
        invoice.sudo().action_post()

    def action_done(self):
        for line in self.order_line:
            for inv in line.invoice_lines:
                if inv.move_id.state != 'posted':
                    raise ValidationError(_('You cannot set a Part Sales to Done if the invoice is not posted.'))
        self.write({
            'state':'done',
            'done_uid': self.env.uid,
            'done_date': datetime.now()
        })

    def _show_cancel_wizard(self):
        return False