# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError
from odoo.fields import Command

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrder(models.Model):
    _inherit = "tw.work.order"
    # 7: defaults methods

    # 8: fields
    amount_commission = fields.Float(string='Amount', default=0)
    
    # 9: relation fields
    mediator_id = fields.Many2one('res.partner', string='Mediator')

    # 10: constraints & sql constraints
    @api.constrains('amount_commission','mediator_id')
    def _validate_amount_commission(self):
        for record in self:
            if record.amount_commission > 0 and not record.mediator_id:
                raise ValidationError('Mediator harus diisi jika Amount Commission lebih dari 0!')
            if record.mediator_id and record.amount_commission <= 0:
                raise ValidationError('Amount commission harus lebih besar dari 0 jika ada Mediator!')

    @api.onchange('mediator_id')
    def _onchange_mediator_id(self):
        self.amount_commission = False

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_view_invoice(self, invoices=False):
        if not invoices:
            invoices = self.mapped('invoice_ids')
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_out_invoice_type')
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            # 'default_move_type': 'out_invoice', #context may be both out and in
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_shipping_id.id,
                'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
                'default_invoice_origin': self.name,
            })
        action['context'] = context
        return action

    # 14: private methods
    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:            
            invoices = order.order_line.sudo().invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
            invoice_commission = self.env['account.move'].search([
                ('invoice_origin', '=', order.name),
                ('move_type', 'in', ('in_invoice', 'in_refund'))
            ])
            order.invoice_ids = invoices + invoice_commission
            order.invoice_count = len(invoices) + len(invoice_commission)

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        moves += self._create_commission_invoice()
        return moves

    def _create_commission_invoice(self):
        move = self.env['account.move']
        if self.amount_commission > 0:
            inv_commission = False
            account_setting_obj = self.company_id.branch_setting_id.account_setting_id
            if not account_setting_obj.journal_wo_commission_id:
                raise Warning('Konfigurasi Journal Commission WO belum disetting!')
            if not self.mediator_id:
                raise Warning('Mediator belum diisi!')
            if not account_setting_obj.journal_wo_commission_id.default_debit_account_id.id:
                raise Warning('Konfigurasi default debit account pada journal %s belum disetting!' %(account_setting_obj.journal_wo_commission_id.name))

            prefix = self.company_id.code
            code = account_setting_obj.journal_wo_commission_id.code

            inv_commission = self._prepare_invoice()
            inv_commission.update({
                'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
                'move_type': 'in_invoice',
                'journal_id': account_setting_obj.journal_wo_commission_id.id,
                'partner_id': self.mediator_id.id,
                'partner_shipping_id': self.mediator_id.id,
                'invoice_line_ids': []
            })

            line_vals = []
            line_obj = self.env['tw.work.order.line']
            if self.amount_commission:
                line_vals.append(Command.create({
                    'name': 'Hutang Komisi %s' % str(self.name),
                    'product_id': False,
                    'discount': 0,
                    'quantity': 1,
                    'account_id': account_setting_obj.journal_wo_commission_id.default_debit_account_id.id,
                    'price_unit': self.amount_commission,
                    'tax_ids': False
                    # ? Dimatikan, karena PPH baru wajib dibuat ketika pembayaran, 
                    # ? walaupun sebenarnya ada kebutuhan dari tim pajak untuk melihat PPH mana yang belum dibayar
                    # 'price_unit': line.amount_commission / line.product_qty,
                    # 'tax_ids': [Command.set([line.commission_tax_id.id])]
                }))
            inv_commission['invoice_line_ids'] = line_vals
            move = self._create_account_invoices(inv_commission, final=True)
        return move
        

    
