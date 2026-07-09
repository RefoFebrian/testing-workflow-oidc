from datetime import datetime
from ipaddress import ip_address
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.tools import (
    float_is_zero,
)

class SaleOrder(models.Model):
    _name = "tw.sale.order"
    _inherit = ["sale.order", "mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _description = "Sale Order"

    def _get_default_date(self):
        return datetime.now()
    
    def _get_default_main_dealer_code(self):
        return self.env['res.company'].get_default_main_dealer_code()
    
    state = fields.Selection(selection_add=[
        ('done',"Done"),
        ('unused',"Unused"),
    ], string="Status", readonly=True, copy=False, tracking=3, default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    amount_invoiced = fields.Monetary(string="Already invoiced", compute='_compute_amount_invoiced')
    invoice_status = fields.Selection(
        string="Invoice Status",
        compute='_compute_invoice_status',
        store=True,
    )

    # Audit Trail Fields
    confirm_uid = fields.Many2one('res.users', 'Confirmed by')
    confirm_date = fields.Datetime('Confirmed on')
    done_date = fields.Datetime('Done on')
    cancel_date = fields.Datetime('Cancelled on')
    cancel_uid = fields.Many2one('res.users', 'Cancelled by')
    done_uid = fields.Many2one('res.users', 'Done by')

    company_id = fields.Many2one('res.company','Branch', domain="[('parent_id', '!=', False)]")
    location_id = fields.Many2one('stock.location', string='Location', domain="[('usage','=','internal'),'|',('company_id','=',company_id),('company_id','=',False)]")
    pricelist_id = fields.Many2one(comodel_name='product.pricelist',string="Pricelist",compute='_compute_pricelist_id',store=True, readonly=False, precompute=True, check_company=True, tracking=1,domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",help="If you change the pricelist, only newly added lines will be affected.")
    order_line = fields.One2many(comodel_name='tw.sale.order.line',inverse_name='order_id',string="Order Lines")
    transaction_ids = fields.Many2many(comodel_name='payment.transaction',relation='tw_sale_order_tw_transaction_rel', column1='order_id', column2='transaction_id',string="Transactions")
    tag_ids = fields.Many2many(comodel_name='crm.tag',relation='tw_sale_order_tw_tag_rel', column1='order_id', column2='tag_id',string="Tags")
    picking_ids = fields.One2many('stock.picking', 'sale_order_id', string='Transfers')
    product_category_ids = fields.Many2many(
        comodel_name='product.category',
        relation='tw_sale_order_product_categ_rel', column1='sale_order_id', column2='product_category_id',
        compute='_compute_product_category_ids',
        string="Product Category")

    @api.depends('division')
    def _compute_product_category_ids(self):
        self.product_category_ids = False
        for order in self:
            if order.division:
                order.product_category_ids = [(6, 0, self.env['product.category'].get_child_ids(order.division))]

    @api.depends('state', 'order_line.qty_to_invoice', 'order_line.qty_invoiced', 'order_line.product_uom_qty')
    def _compute_invoice_status(self):
        """
        Compute invoice_status for tw.sale.order based on tw.sale.order.line.
        - 'no': Nothing to invoice (state is draft/cancel or no lines to invoice)
        - 'to invoice': At least one line has qty_to_invoice > 0
        - 'invoiced': All lines have been fully invoiced
        """
        for order in self:
            if order.state in ('draft', 'sent', 'cancel'):
                order.invoice_status = 'no'
                continue
            
            lines = order.order_line.filtered(lambda line: not line.display_type and not line.is_downpayment)
            
            if not lines:
                order.invoice_status = 'no'
                continue
            
            # Check if there's anything to invoice
            total_to_invoice = sum(lines.mapped('qty_to_invoice'))
            total_qty = sum(lines.mapped('product_uom_qty'))
            total_invoiced = sum(lines.mapped('qty_invoiced'))
            
            if float_is_zero(total_qty, precision_digits=2):
                order.invoice_status = 'no'
            elif total_to_invoice > 0:
                order.invoice_status = 'to invoice'
            elif total_invoiced >= total_qty:
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'no'

    @api.depends('company_id', 'division')
    def _compute_pricelist_id(self):
        for order in self:
            if order.state != 'draft':
                continue

            order = order.with_company(order.company_id)
            order.pricelist_id = order._get_pricelist()
    
    @api.depends('partner_id', 'company_id', 'division')
    def _compute_amount_invoiced(self):
        for order in self:
            if not order.partner_id or not order.company_id or not order.division:
                order.amount_invoiced = 0.0
                continue
            
        # Find all invoices for this customer and branch that are still outstanding
        domain = [
            ('partner_id', '=', order.partner_id.id),
            ('company_id', '=', order.company_id.id),
            ('division', '=', order.division),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '!=', 'paid'),
            ('invoice_line_ids.sale_order_line_ids', '!=', False),
        ]
        
        invoices = self.env['account.move'].search(domain)
        
        # Calculate total outstanding amount
        total_outstanding = sum(
            inv.amount_residual_signed 
            for inv in invoices 
            if not float_is_zero(
                inv.amount_residual, 
                precision_rounding=inv.currency_id.rounding
            )
        )
        
        order.amount_invoiced = total_outstanding


    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            warehouse_obj = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], order="id DESC", limit=1)
            if warehouse_obj:
                if not self.warehouse_id:
                    self.warehouse_id = warehouse_obj.id
                if not self.location_id:
                    self.location_id = warehouse_obj.lot_stock_id.id

    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.location_id:
            self.order_line._onchange_product_id_warning()
    
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('company_id'):
                branch_src = self.env['res.company'].suspend_security().search([('id','=',vals['company_id'])],limit=1)
                seq_name = self.env['ir.sequence'].with_company(branch_src).get_sequence_code('SO', branch_src.code)
                vals['name'] = seq_name
        return super(SaleOrder, self).create(vals_list)
    
    def write(self, vals):
        if vals.get('picking_ids'):
            pass
        return super().write(vals)

    def unlink(self):
        for record in self:
            raise Warning('Warning! \nCannot delete records!')
        return super(SaleOrder, self).unlink()
    
    def action_confirm(self):
        if self.state != 'approved':
            raise UserError(f'Silakan refresh halaman browser Anda. State sudah {self._get_state_value()}')
        self._prepare_confirmation()
        res = super(SaleOrder, self.with_context(model_name='tw.sale.order')).action_confirm()

        # Unreserve picking agar user bisa assign manual
        for picking in self.picking_ids.filtered(lambda p: p.state == 'assigned'):
            picking.do_unreserve()

        return res

    def action_renew_price(self):
        for sol in self.order_line:
            if sol.product_id:
                sol.get_product_price()
    
    def action_unused(self):
        if self.state == 'unused':
            raise UserError(f'Silakan refresh halaman browser Anda. State sudah {self._get_state_value()}')
        self.write({ 'state':'unused' })

    def action_done(self):
        """Mark Sale Order as done when both invoices are paid and pickings are done."""
        if self.state == 'done':
            return
        
        # Check if all invoices are paid
        invoices = self.invoice_ids.filtered(lambda inv: inv.state == 'posted')
        all_invoices_paid = all(inv.payment_state in ('paid', 'in_payment', 'reversed') for inv in invoices) if invoices else False
        
        # Check if all pickings are done
        pickings = self.picking_ids.filtered(lambda p: p.state != 'cancel')
        all_pickings_done = all(p.state == 'done' for p in pickings) if pickings else False
        
        # Only set to done if both conditions are met
        if all_invoices_paid and all_pickings_done:
            self.suspend_security().write({
                'state': 'done',
                'done_uid': self.env.uid,
                'done_date': datetime.now(),
            })

    def action_set_amount_invoiced(self):
        total_inv = self.invoice_total()
        if not total_inv:
            total_inv = 0

        self.suspend_security().write({ 'amount_invoiced': total_inv })
    
    def get_transaction(self, model):
        transaction_obj = self.env[model].search([
            ('model_id.model', '=', self.__class__.__name__),
            ('transaction_id', '=', self.id),
            ('state', '!=', 'cancel')
        ])
        return transaction_obj
    
    def reverse(self):
        picking_obj = self.get_transaction('stock.picking')
        picking_ids = [picking.id for picking in picking_obj]

        move_obj = self.env['stock.move'].search([
            ('picking_id','in',picking_ids),
            ('origin_returned_move_id','!=',False),
            ('state','!=','cancel')
        ])
        if move_obj:
            return True
        return False
    
    def renew_available(self):
        for so_line in self.order_line:
            quantity_available = so_line.get_quantity_available(self.company_id.id, so_line.product_id.id, self.division, self.location_id.id)
            so_line.qty_available = quantity_available
    
    def action_print_invoice_pdf(self):
        self.ensure_one()
        invoices = self.invoice_ids.filtered(lambda inv: inv.state == 'posted' and inv.move_type == 'out_invoice')
        if not invoices:
            raise Warning("Belum ada invoice yang bisa di-print. Silahkan buat invoice terlebih dahulu.")
        return self.env.ref('tw_sale.invoice_sale_order_report').report_action(self.id)
    
    def get_branch_journal_config(self):
        branch_setting_obj = self.env['tw.branch.setting'].search([('company_id','=',self.company_id.id)])
        if not branch_setting_obj:
            raise Warning("Attention! The Branch Sales Journal hasn't been Created. Please Set it up First.")
        account_setting_obj = branch_setting_obj.account_setting_id
        if not account_setting_obj:
            raise Warning("Attention! The Account Setting hasn't been Created. Please Set it up First for {self.company_id.name}.")

        journal_sales = account_setting_obj.get_account_setting('journal_sales_unit_id', raise_if_none=True)
        if self.division == 'Sparepart':
            journal_sales = account_setting_obj.get_account_setting('journal_sales_sparepart_id', raise_if_none=True)
        
        journal_list = {
            'journal_sales': journal_sales
        }
        return journal_list
    
    def get_pricelist(self):
        #? Re-Take pricelist, just in case the SO is created before pricelist configured
        if not self.pricelist_id:
            self.pricelist_id = self._get_pricelist()

        current_pricelist = self.pricelist_id 
        if not current_pricelist:
            raise Warning("'Price List Jual %s' untuk cabang %s belum di setting. Silahkan lakukan konfigurasi di branch setting."%(self.division, self.company_id.name))
        
        return current_pricelist
    
    def action_create_invoice(self):
        branch = self.company_id
        
        if (self.division == 'Unit' and branch.is_so_unit_pick_then_invoice) or (self.division == 'Sparepart' and branch.is_so_sparepart_pick_then_invoice):  
            pickings = self.picking_ids.filtered(lambda p: p.picking_type_id.name == 'Pick' and p.picking_type_id.code == 'internal' and p.state == 'done')
            if not pickings:
                raise Warning("Anda harus menyelesaikan pengambilan barang (Pick) terlebih dahulu, sebelum membuat invoice.")
        
        invoices = self.sudo()._create_invoices()
        for invoice in invoices:
            invoice.line_ids.suspend_security().write({
                'company_id': self.company_id.id,
                'division': self.division,
            })
            invoice.sudo().action_post()
    
    def _prepare_invoice(self):
        journal_obj = self.get_branch_journal_config().get('journal_sales')
        self.suspend_security().write({
            'journal_id': journal_obj.id,
        })
        prepare_invoice = super()._prepare_invoice()
        
        code = journal_obj.code
        prefix = self.company_id.code
        
        prepare_invoice.update({
            'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
            'date': fields.Date.today(),
            'company_id': self.company_id.id,
            'division': self.division,
            'invoice_date': self.date_order,
            'ref': self.name,
            'invoice_line_ids':[],
            'line_ids':[],
        })

        return prepare_invoice
    
    def _get_pricelist(self):
        current_pricelist=False
        if self.division =='Unit':
            current_pricelist = self.company_id.branch_setting_id.pricelist_sale_unit_id
        elif self.division == 'Sparepart':  
            current_pricelist = self.company_id.branch_setting_id.pricelist_sale_sparepart_id
        return current_pricelist
    
    def _action_cancel(self):
        if self.cancel_uid or self.cancel_date:
            raise Warning("Transaksi telah dilakukan pembatalan oleh %s pada %s" %(self.cancel_uid, self.cancel_date))
        
        sale_order_cancel = super(SaleOrder,self)._action_cancel()
        self.write({
            'cancel_uid': self.env.uid,
            'cancel_date': datetime.now()
        })
        return sale_order_cancel
    
    def _prepare_confirmation(self):  
        if self.state == 'sent':
            raise Warning("Silakan refresh halaman ini karena telah dilakukan Confirm")      
        self._validate_order()
        self.write({
            'date_order': datetime.now(),
            'state': 'sent',
            'confirm_uid': self.env.uid,
            'confirm_date': datetime.now()
        })
    
    def _validate_order(self):
        self.renew_available()
        self.order_line._validate_order_line()
    
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

        return self.env['tw.sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)