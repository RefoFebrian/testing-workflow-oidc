# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import float_is_zero, groupby

# 5: local imports

# 6: Import of unknown third party lib

class TwSaleOrder(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    finco_id = fields.Many2one('res.partner', 'Finance Company', domain=[('category_id.name', '=', 'Finance Company')])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.finco_id = False
        super()._onchange_company_id()

    @api.depends('partner_id', 'finco_id')
    def _compute_payment_term_id(self):
        super()._compute_payment_term_id()
        for order in self:
            order = order.with_company(order.company_id)
            if order.finco_id:
                order.payment_term_id = order.finco_id.property_payment_term_id.id

    @api.onchange('payment_type_id')
    def _onchange_payment_type_id(self):
        if self.payment_type_id and self.payment_type_id.value != 'Credit':
            self.finco_id = False

    @api.onchange('finco_id')
    def _onchange_finco_id(self):
        for line in self.order_line:
            if not self.finco_id:
                line.finco_incentive = False
                line.finco_incentive_tax = False
                line.finco_po_date = False
                line.finco_po_number = False
                line.tenor = False
                line.installment = False
                line.downpayment = False
                
    # 12: override methods
    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        if self.finco_id:
            moves += self._create_incentive_finco_invoice()
        return moves
    
    def _prepare_main_invoice(self):
        invoice_vals = super()._prepare_main_invoice()
        if self.finco_id:
            invoice_vals['partner_id'] = self.finco_id.id
            invoice_vals['partner_shipping_id'] = self.finco_id.id
        return invoice_vals

    def _create_incentive_finco_invoice(self):
        move = self.env['account.move']
        if self.finco_id:
            self.ensure_one()
            invoice_vals = self._prepare_incentive_finco_invoice()
            move = self._create_account_invoices(invoice_vals, final=True)
        return move
        
    def _prepare_incentive_finco_invoice(self):
        account_conf = self.company_id.branch_setting_id.account_setting_id
        journal_finco = account_conf.journal_dso_incentive_finco_id
        if not journal_finco:
            raise Warning(_("Journal Incentive Finco belum dikonfigurasi di Account Setting ini!\nSilakan konfigurasikan di menu Account Setting."))
        
        incentive_finco_invoice_vals = self._prepare_invoice()
        code = journal_finco.code
        prefix = self.company_id.code
        incentive_finco_invoice_vals.update({
            'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
            'move_type': 'out_invoice',
            'journal_id': journal_finco.id,
            'partner_id': self.finco_id.id,
            'partner_shipping_id': self.finco_id.id
        })
        
        invoice_line_ids = []
        order_line = self.order_line.filtered(lambda l: l.item_type == 'main')
        for product, record in groupby(order_line, key=lambda x: x.product_id):
            line = record[0]
            price_unit = qty = 0
            tax_ids = []
            dsol_ids = []
            for rec in record:
                incentive_finco = rec._get_incentive_finco_amount()
                price_unit += incentive_finco.amount
                qty += rec.product_uom_qty
                tax_ids += incentive_finco.incentive_finco_line_id.tax_ids.ids
                dsol_ids.append(rec.id)
            
            invoice_line_ids.append(Command.create(line._prepare_invoice_line(**{
                'name': f'Incentive {product.default_code}',
                'price_unit': price_unit / qty,
                'product_id': False,
                'discount': 0,
                'quantity': qty,
                'account_id': journal_finco.default_credit_account_id.id,
                'tax_ids': [Command.set(list(set(tax_ids)))]
            })))

        incentive_finco_invoice_vals['invoice_line_ids'] = invoice_line_ids
                
        return [incentive_finco_invoice_vals]

    # 13: action methods

    # 14: private methods
    def _prepare_partner_cdb(self):
        cdb_vals = super()._prepare_partner_cdb()
        cdb_vals.update({
            'finco_id': self.finco_id.id,
        })
        return cdb_vals
    
