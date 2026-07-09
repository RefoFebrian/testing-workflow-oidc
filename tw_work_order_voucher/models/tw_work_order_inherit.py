# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderVoucher(models.Model):
    _inherit = "tw.work.order"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    sales_voucher_ids = fields.Many2many('tw.sales.voucher', 'tw_work_order_sales_voucher_rel', 'work_order_id', 'sales_voucher_id', string='Tunas Honda Voucher')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('lot_id')
    def _onchange_sales_voucher_ids(self):
        self.sales_voucher_ids = [(5, 0, 0)]
        if self.lot_id and self.type_id and self.type_id.value == 'REG' and self.customer_stnk_id:
            invoice_obj = self.env['account.move'].suspend_security().search([
                ('partner_id', '=', self.customer_stnk_id.id),
                ('journal_id.code', '=', 'HV'),
                ('payment_state', '=', 'not_paid')
            ], limit=1)
            if invoice_obj:
                voucher_obj = self.env['tw.sales.voucher'].suspend_security().search([
                    ('lot_id', '=', self.lot_id.id),
                    ('residual_amount', '>', 0)
                ])
                self.sales_voucher_ids = voucher_obj

    # 12: override methods
    
    # 13: action methods
    def action_done(self):
        voucher_obj = self.env['tw.sales.voucher'].suspend_security().search([
            ('lot_id', '=', self.lot_id.id)
        ], limit=1)
        if voucher_obj:
            voucher_obj.write({
                'partner_id': self.customer_stnk_id.id,
                'claimed_transaction_name': self.name
            })
        
        payment_lines = self.env['tw.account.payment.line'].suspend_security().search([
            ('type', '=', 'dr'),
            ('move_line_id.journal_id.code', '=', 'HV'),
            ('payment_id.partner_id', '=', self.customer_stnk_id.id),
            ('payment_id.state', '=', 'paid'),
        ])
        if payment_lines:
            total_amount = sum(payment_lines.mapped('amount'))
            voucher_obj.write({'used_amount': total_amount})
        return super(TwWorkOrderVoucher, self).action_done()
