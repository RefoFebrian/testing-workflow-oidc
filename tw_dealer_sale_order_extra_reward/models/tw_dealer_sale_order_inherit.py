# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, Command, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwDealerSaleOrderInherit(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods

    # 8: fields
    amount_extra_reward = fields.Float(string='Total Extra Reward', store=True, compute='_compute_amounts_extra_reward', help='Total Extra Reward')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('order_line', 'order_line.amount_extra_reward')
    def _compute_amounts_extra_reward(self):
        super()._compute_amounts()
        for order in self:
            amount_extra_reward = sum([line.amount_extra_reward for line in order.order_line])
            order.amount_extra_reward = amount_extra_reward

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for order in self:
            if order.partner_id:
                for line in order.order_line:
                    line.extra_reward_partner_id = order.partner_id.id

    # 12: override methods

    # 13: action methods

    # 14: private methods
    
    def _prepare_sumary_discount_data(self, product_id, lines):
        data = super()._prepare_sumary_discount_data(product_id, lines)
        data.update({
            'extra_reward': sum(lines.mapped('amount_extra_reward'))
        })
        return data
    
    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        moves += self._create_extra_reward_invoice()
        return moves

    def _create_extra_reward_invoice(self):
        move = self.env['account.move']
        if self.amount_extra_reward > 0:
            inv_extra_reward = False
            account_setting_obj = self.company_id.branch_setting_id.account_setting_id
            journal_extra_reward = account_setting_obj.journal_dso_extra_reward_id
            if not journal_extra_reward:
                raise Warning('Konfigurasi Journal Extra Reward belum disetting!')
            if not journal_extra_reward.default_debit_account_id.id:
                raise Warning('Konfigurasi default debit account pada journal %s belum disetting!' %(journal_extra_reward.name))
            
            inv_extra_reward = self._prepare_invoice()

            prefix = self.company_id.code
            code = journal_extra_reward.code or 'CB'
            inv_extra_reward.update({
                'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
                'move_type': 'in_invoice',
                'journal_id': journal_extra_reward.id,
                'partner_id': self.partner_invoice_id.id,
                'partner_shipping_id': self.partner_shipping_id.id,
                'invoice_line_ids': []
            })

            line_vals = []
            order_line = self.order_line.filtered(lambda l: l.item_type == 'main')
            for line in order_line:
                if line.amount_extra_reward and line.product_qty:
                    if not line.extra_reward_tax_id:
                        raise Warning('Konfigurasi Pajak Extra Reward belum disetting!')
                    # Use commission_tax_id if available, otherwise fallback to extra_reward_tax_id
                    tax = line.commission_tax_id or line.extra_reward_tax_id
                    tax_ids = [Command.set([tax.id])] if tax else [Command.set([])]
                    line_vals.append(Command.create(line._prepare_invoice_line(**{
                            'name': 'Cashback %s' % str(line.product_id.name),
                            'price_unit': line.amount_extra_reward / line.product_qty,
                            'product_id': False,
                            'discount': 0,
                            'quantity': line.product_qty,
                            'account_id': journal_extra_reward.default_debit_account_id.id,
                            'tax_ids': tax_ids
                        })))
            inv_extra_reward['invoice_line_ids'] = line_vals
            move = self._create_account_invoices(inv_extra_reward, final=True)
        return move