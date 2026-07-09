# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class AccountMoveInherit(models.Model):
    _inherit = "account.move"
    
    # 7: defaults methods

    # 8: fields
    
    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # @api.model_create_multi
    # def create(self,vals_list):
    #     move_obj = super().create(vals_list)
    #     # Sync cost method template to new companies
    #     return move_obj
    
    # def write(self,vals):

    # 13: action methods
    def _post(self, soft=True):
        for move in self:
            move.check_price_diff_undelivered_move()
        posted = super(AccountMoveInherit, self.sudo().with_context(skip_cogs_reconciliation=True))._post(soft)
        return posted
    
    def check_price_diff_undelivered_move(self):
        if self.sudo().stock_valuation_layer_ids:
            stock_move = self.env['stock.move'].search([('account_move_ids','in',self.id)])
            if stock_move:
                stock_journal = stock_move.product_id.with_company(self.company_id).categ_id.property_stock_journal
                if self.journal_id.id == stock_journal.id:
                    if stock_move.sale_order_line_id:
                        cogs = stock_move.sale_order_line_id.cogs
                        aml = self.line_ids.filtered(lambda x: x.credit > 0)[0]
                        if aml._eligible_for_cogs():
                            qty = abs(aml.quantity) if aml.quantity else 1
                            price = aml.credit
                            price_per_unit = price / qty
                            if cogs != price_per_unit:
                                self._create_price_diff_move(self, aml, cogs, price_per_unit)
    
    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        vals_list = super()._stock_account_prepare_anglo_saxon_out_lines_vals()
        for vals in vals_list:
            move_id = vals.get('move_id')
            if move_id:
                move = self.env['account.move'].browse(move_id)
                if move:
                    if not vals.get('company_id'):
                        vals['company_id'] = move.company_id.id
                    if not vals.get('division'):
                        vals['division'] = move.division
                        
        return vals_list

    def _create_price_diff_move(self, move, aml, cogs, price):
        # Retrieve accounts needed to generate the COGS.
        accounts = aml.product_id.product_tmpl_id.with_company(self.company_id).get_product_accounts(fiscal_pos=move.fiscal_position_id)
        debit_interim_account = accounts['stock_output']
        credit_expense_account = accounts['expense'] or move.journal_id.default_account_id
        if not debit_interim_account or not credit_expense_account:
            return

        # Compute accounting fields.
        sign = 1
        price_unit = cogs - price
        amount_currency = price_unit
        if move.currency_id.is_zero(amount_currency) or float_is_zero(price_unit, precision_digits=move.currency_id.decimal_places):
            return

        # Prepare move values
        move_vals = {
            'move_type': 'entry',
            'date': move.date,
            'ref': _('Price Difference - %s') % move.ref,
            'journal_id': move.journal_id.id,
            'division': move.division,
            'period_id': move.period_id.id,
            'partner_id': move.partner_id.id,
            'company_id': move.company_id.id,
            'line_ids': [
                # Debit line (interim account)
                (0, 0, {
                    'name': _('Price Difference - %s') % aml.name[:64],
                    'division': aml.division,
                    'company_id': move.company_id.id,
                    'partner_id': move.commercial_partner_id.id,
                    'product_id': aml.product_id.id,
                    'product_uom_id': aml.product_uom_id.id,
                    'quantity': aml.quantity,
                    'price_unit': price_unit,
                    'debit': abs(amount_currency) if amount_currency > 0 else 0,
                    'credit': abs(amount_currency) if amount_currency < 0 else 0,
                    'account_id': debit_interim_account.id,
                    'tax_ids': [(6, 0, [])],
                }),
                # Credit line (expense account)
                (0, 0, {
                    'name': _('Price Difference - %s') % aml.name[:64],
                    'division': aml.division,
                    'company_id': move.company_id.id,
                    'partner_id': move.commercial_partner_id.id,
                    'product_id': aml.product_id.id,
                    'product_uom_id': aml.product_uom_id.id,
                    'quantity': aml.quantity,
                    'price_unit': -price_unit,
                    'debit': abs(amount_currency) if amount_currency < 0 else 0,
                    'credit': abs(amount_currency) if amount_currency > 0 else 0,
                    'account_id': credit_expense_account.id,
                    'tax_ids': [(6, 0, [])],
                }),
            ]
        }

        # Create the move
        diff_move = self.env['account.move'].create(move_vals)
        
        # Post the move
        diff_move.sudo().action_post()
        
        return diff_move