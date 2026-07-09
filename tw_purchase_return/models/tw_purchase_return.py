# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from odoo.tools import (
    float_is_zero,
)

_logger = logging.getLogger(__name__)

class TwPurchaseReturn(models.Model):
    _name = "tw.purchase.return"
    _inherit = "sale.order"
    _description = "Purchase Return"
    _order = "id desc"

    # Override sale.order fields
    name = fields.Char(
        string='Return Reference',
        required=True,
        copy=False,
        index=True,
        default='New',
        readonly=True
    )
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_compute_amount_all')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_compute_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount_all')
    date_return = fields.Datetime(string='Return Date', default=fields.Datetime.now)
    invoice_date = fields.Datetime(string='Invoice Date')
    confirm_uid = fields.Many2one('res.users', 'Confirmed by')
    confirm_date = fields.Datetime('Confirmed on')
    done_uid = fields.Many2one('res.users', 'Done by')
    done_date = fields.Datetime('Done on')

    notes = fields.Text('Notes')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    state = fields.Selection(selection_add=[
        ('sale', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft')
    
    invoice_status = fields.Selection(
        string="Invoice Status",
        compute='_compute_invoice_status',
        store=True,
    )

    partner_id = fields.Many2one('res.partner', string='Supplier', change_default=True, tracking=True)
    invoice_id = fields.Many2one('account.move', string='Purchase Invoice', 
        domain="""[
            ('partner_id', '=', partner_id),
            ('company_id', '=', company_id),
            ('move_type', '=', 'in_invoice'),
            ('division', '=', division),
            ('invoice_line_ids.purchase_line_id', '!=', False),
            ('payment_state', '=', 'paid')
        ]""", 
        tracking=True,
        help="Select an invoice from a purchase order"
    )
    order_line = fields.One2many('tw.purchase.return.line', 'order_id', string='Return Lines', copy=True, auto_join=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', compute='_compute_purchase_order', store=True)
    available_product_ids = fields.Many2many('product.product', string='Available Products', compute='_compute_available_products')
    tag_ids = fields.Many2many('crm.tag', 'tw_purchase_return_tag_rel', 'return_id', 'tag_id', string='Tags')
    transaction_ids = fields.Many2many(comodel_name='payment.transaction',relation='tw_purchase_return_tw_transaction_rel', column1='order_id', column2='transaction_id',string="Transactions")
    picking_ids = fields.One2many('stock.picking', 'purchase_return_id', string='Transfers')

    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                company_id = vals.get('company_id') or self.env.company.id
                company = self.env['res.company'].browse(company_id)
                vals['name'] = self.env['ir.sequence'].with_company(company).get_sequence_code('RB', company.code)
        return super(TwPurchaseReturn, self).create(vals_list)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.partner_id = False
        
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.invoice_id = False
        self.payment_term_id = False
        if self.partner_id:
            self.payment_term_id = self.partner_id.property_supplier_payment_term_id

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        self.invoice_date = False
        self.order_line = False
        if self.invoice_id:
            self.invoice_date = self.invoice_id.invoice_date
                
    @api.depends('invoice_id')
    def _compute_purchase_order(self):
        for rec in self:
            rec.purchase_order_id = rec.invoice_id.invoice_line_ids.mapped('purchase_line_id.order_id')[:1]

    @api.depends('purchase_order_id')
    def _compute_available_products(self):
        for rec in self:
            if rec.purchase_order_id:
                rec.available_product_ids = rec.purchase_order_id.order_line.mapped('product_id')
            else:
                rec.available_product_ids = False

    def _compute_invoice_status(self):
        """
        Compute invoice_status for tw.purchase.return based on lines.
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


    def action_view_purchase(self):
        """
        View related purchase order
        """
        self.ensure_one()
        if not self.purchase_id:
            raise UserError(_('No purchase order is related to this return.'))
            
        return {
            'name': _('Purchase Order'),
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'res_id': self.purchase_id.id,
            'context': {'form_view_initial_mode': 'edit'}
        }
    
    def unlink(self):
        for return_order in self:
            if return_order.state not in ('draft', 'cancel'):
                raise UserError(_('You can only delete draft or cancelled returns.'))
        return super(TwPurchaseReturn, self).unlink()
    
    def _validate_order(self):
        """Validate order before confirmation. Override this in approval modules."""
        if not self.order_line:
            raise UserError(_('Silakan isi detail line terlebih dahulu sebelum melanjutkan proses.'))

    def action_confirm(self):
        if self.state != 'approved':
            raise UserError(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        self._validate_order()
        self._prepare_confirmation()
        return super(TwPurchaseReturn, self.with_context(model_name='tw.purchase.return')).action_confirm()

    def action_create_invoice(self):
        invoices = self._create_invoices()
        for invoice in invoices:
            invoice.line_ids.suspend_security().write({
                'company_id': self.company_id.id,
                'division': self.division,
            })
            invoice.sudo().action_post()
    
    def get_branch_journal_config(self):
        branch_setting_obj = self.env['tw.branch.setting'].search([('company_id','=',self.company_id.id)])
        if not branch_setting_obj:
            raise Warning("Attention! The Branch Sales Journal hasn't been Created. Please Set it up First.")
        account_setting_obj = branch_setting_obj.account_setting_id
        if not account_setting_obj:
            raise Warning("Attention! The Account Setting hasn't been Created. Please Set it up First for {self.company_id.name}.")

        journal_purchase_return = account_setting_obj.get_account_setting('journal_purchase_return_id')
        if not journal_purchase_return:
            raise Warning(f"Attention!\n Journal Purchase Return for branch {self.company_id.name} is Incomplete. Please Set it up First.")
        
        journal_list = {
            'journal_purchase_return': journal_purchase_return
        }
        return journal_list
    
    def _prepare_confirmation(self):   
        self.suspend_security().write({
            'state': 'sent',
            'confirm_uid': self.env.uid,
            'confirm_date': datetime.now()
        })

    def action_done(self):
        """Mark Purchase Return as done when both invoices are paid and pickings are done."""
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
    
    def _prepare_invoice(self):
        journal_obj = self.get_branch_journal_config().get('journal_purchase_return')
        self.suspend_security().write({
            'journal_id': journal_obj.id,
        })
        prepare_invoice = super()._prepare_invoice()
        
        code = journal_obj.code
        prefix = self.company_id.code
        
        prepare_invoice.update({
            'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
            'company_id': self.company_id.id,
            'division': self.division,
            'invoice_date': self.date_order,
            'ref': self.name,
            'move_type': 'out_invoice',
            'invoice_line_ids':[],
            'line_ids':[],
        })

        return prepare_invoice
    
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

        return self.env['tw.purchase.return.line'].browse(invoiceable_line_ids + down_payment_line_ids)