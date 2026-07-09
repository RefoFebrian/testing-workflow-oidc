# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.fields import Command

class SaleOrderInherit(models.Model):
    _inherit = "tw.sale.order"

    def action_create_invoice(self):
        res = super().action_create_invoice()
        if self.division == 'Unit':
            self.suspend_security().action_invoice_bb_jual_create()
        return res

    def action_invoice_bb_jual_create(self):
        """Create the invoice associated to the Blind Bonus Jual."""
        self.ensure_one()
        
        # Validate blind bonus amount
        if not self.company_id.branch_setting_id.sale_blind_bonus_amount or self.company_id.branch_setting_id.sale_blind_bonus_amount <= 0:
            raise Warning(_('Amount Blind Bonus Main Dealer tidak boleh <= 0, silahkan konfigurasi ulang di branch setting'))
        
        # Prepare and create the invoice
        invoice_vals = self._prepare_blind_bonus_invoice()
        invoice = self.env['account.move'].with_context(
            default_move_type='in_invoice',
            skip_is_manually_modified=True
        ).with_company(self.company_id.id).suspend_security().create(invoice_vals)
        
        invoice.sudo().action_post()
        return invoice.id

    def _get_additional_cancel_account_moves(self):
        moves = super()._get_additional_cancel_account_moves()
        self.ensure_one()

        blind_bonus_journal = self.company_id.branch_setting_id.account_setting_id.journal_sale_blind_bonus_id
        if self.division != 'Unit' or not blind_bonus_journal:
            return moves

        blind_bonus_moves = self.env['account.move'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('journal_id', '=', blind_bonus_journal.id),
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('reversed_entry_id', '=', False),
            '|',
            ('invoice_origin', '=', self.name),
            ('ref', '=', self.name),
        ])
        return moves | blind_bonus_moves
        
    def _prepare_blind_bonus_invoice(self):
        """Prepare the dict of values to create the new blind bonus invoice."""
        self.ensure_one()
        
        # Get branch settings
        branch_setting = self.company_id.branch_setting_id
        if not branch_setting:
            raise Warning(
                "Branch setting is not set for this branch.\n"
                "- Go to the Master Branch Setting.\n"
                "- Set the branch setting to proceed."
            )
            
        # Get account settings
        account_setting = branch_setting.account_setting_id
        if not account_setting:
            raise Warning(
                "Account setting is not set for this branch.\n"
                "- Go to the Master Branch Setting.\n"
                "- Set the 'Account Setting' to proceed."
            )
            
        # Get journal configuration
        journal = account_setting.get_account_setting('journal_sale_blind_bonus_id', raise_if_none=True)
            
        # Calculate total quantity from order lines
        total_qty = sum(line.product_uom_qty for line in self.order_line)
        
        # Prepare invoice line values
        invoice_line_vals = {
            'name': _('Blind Bonus Jual %s') % self.name,
            'quantity': total_qty,
            'price_unit': branch_setting.sale_blind_bonus_amount,
            'account_id': journal.default_debit_account_id.id,
            'company_id': self.company_id.id,
            'division': self.division,
            'sale_order_line_ids': [Command.link(line.id) for line in self.order_line],
        }
        
        # Prepare invoice values
        return {
            'name': self.env['ir.sequence'].get_sequence_code(journal.code, self.company_id.code),
            'move_type': 'in_invoice',
            'invoice_origin': self.name,
            'ref': self.name,
            'partner_id': self.partner_id.id,
            'division': self.division,
            'invoice_date': fields.Date.context_today(self),
            'journal_id': journal.id,
            'currency_id': self.currency_id.id,
            'invoice_line_ids': [(0, 0, invoice_line_vals)],
            'company_id': self.company_id.id,
        }
