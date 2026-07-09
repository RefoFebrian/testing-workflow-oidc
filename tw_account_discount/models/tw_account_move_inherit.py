# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
from re import I
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWAccountMove(models.Model):
    _inherit = "account.move"
    
    # 7: defaults methods

    # 8: fields
    has_discount = fields.Boolean(readonly=False, store=False, compute='_compute_has_discount')

    # 9: relation fields

    invoice_ids = fields.One2many(  # /!\ invoice_line_ids is just a subset of line_ids.
        'account.move.line',
        'move_id',
        string='Invoice Items',
        copy=False,
        domain=[('display_type', 'in', ('product', 'line_section', 'line_note')), ('product_id', '!=', False)],
    )

    discount_line_ids = fields.One2many(
        comodel_name='account.move.discount',
        inverse_name='move_id',
        string='Discount lines',
        copy=False,
        compute='_compute_discount_line',
        store=True, readonly=False,
    )
    discount_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='move_id',
        string='Discount Entries',
        copy=False,
        domain=[('display_type', '=', 'product'), ('price_unit', '<', 0)],
        store=True
    )
    account_discount_ids = fields.Many2many(
        comodel_name='tw.account.discount',
        relation='tw_account_move_discount_rel',
        column1='move_id', column2='discount_id',
        compute='_compute_account_discount',
        store=False)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id', 'move_type')
    def _compute_account_discount(self):
        for record in self:
            discount_account = record.env['tw.account.discount']._get_discount_account(record.company_id, record.move_type)
            record.account_discount_ids = discount_account.mapped('id')            

    @api.depends('account_discount_ids')
    def _compute_discount_line(self):
        for record in self:
            record.discount_line_ids = [Command.clear()]
            if record.account_discount_ids:
                discount_line_ids = []
                for d in record.account_discount_ids.with_company(record.company_id):
                    discount_line_ids.append(Command.create({
                        'name': d.name,
                        'amount': 0,
                        'company_id': record.company_id.id,
                        'currency_id': record.currency_id.id,
                        'discount_id': d.id,
                        'account_id': d.account_id.id,
                        'tax_ids': [Command.set(d.tax_ids.ids)],
                    }))
                record.discount_line_ids = discount_line_ids
    
    @api.depends('discount_line_ids.amount')
    def _compute_has_discount(self):
        for move in self:
            move.has_discount = any([d.amount > 0 for d in move.discount_line_ids])

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('discount_line_ids'):
                for disc in vals.get('discount_line_ids'):
                    disc_vals = disc[2]
                    if disc_vals['amount'] > 0:
                        vals['invoice_line_ids'] += [self.env['account.move.discount']._prepare_discount_invoice_line(disc_vals)]
        moves = super().create(vals_list)
        # Force computation of tax_totals for each move
        for move in moves:
            if move.is_invoice(include_receipts=True):
                move._compute_tax_totals()
        
        return moves
    
    def write(self, vals):
        if vals.get('discount_line_ids'):
            invoice_line_ids = []
            for disc in vals.get('discount_line_ids'):
                # TODO: this code seems to long to do CRUD operation. It should be optimized.
                # Probably using models account.move.discount create, write, unlink methods overriding
                AccountMoveDiscount = self.env['account.move.discount']
                if disc[0] == 1:
                    # when update account.move.discount the amount invoice_line_ids will be updated,
                    # so automatically the journal entry will be updated.
                    # But when the amount is 0, the invoice_line_ids will be deleted. So does the journal entry.
                    disc_vals = disc[2]
                    invoice_line = AccountMoveDiscount._get_related_invoice_lines(disc[1])
                    if invoice_line:
                        if disc_vals.get('amount') > 0:
                            invoice_line_ids.append(Command.update(invoice_line.id, {'price_unit': -disc_vals['amount']}))
                        elif disc_vals.get('amount') == 0:
                            invoice_line_ids.append(Command.delete(invoice_line.id))
                    elif not invoice_line:
                        if disc_vals.get('amount') > 0:
                            discount_line = AccountMoveDiscount.browse(disc[1]).with_company(self.company_id)
                            disc_vals.update({
                                'company_id': self.company_id.id,
                                'discount_id': discount_line.discount_id.id,
                                'tax_ids': [Command.set(discount_line.tax_ids.ids)],
                            })
                            invoice_line_ids.append(AccountMoveDiscount._prepare_discount_invoice_line(disc_vals))

                elif disc[0] in (2, 3):
                    # if the link account.move.discount is deleted or cuted, the invoice_line_ids will be deleted.
                    invoice_line = AccountMoveDiscount._get_related_invoice_lines(disc[1])
                    if invoice_line:
                        invoice_line_ids.append(Command.delete(invoice_line.id))

                elif disc[0] == 4:
                    # when the account.move.discount is linked, the related invoice_line_ids will be created.
                    discount_lines = AccountMoveDiscount.browse(disc[1]).with_company(self.company_id)
                    for discount_line in discount_lines:
                        if discount_line.amount > 0:
                            move_discount_vals = {
                                'company_id': self.company_id.id,
                                'amount': discount_line.amount,
                                'tax_ids': [Command.set(discount_line.tax_ids.ids)]
                            }
                            invoice_line_ids += [AccountMoveDiscount._prepare_discount_invoice_line(discount_line.id, move_discount_vals)]
                
                elif disc[0] == 5:
                    # when the account.move.discount is clear, the related invoice_line_ids will be removed.
                    discount_lines = AccountMoveDiscount.search(['move_id', '=', self.id])
                    for discount_line in discount_lines:
                        invoice_line = AccountMoveDiscount._get_related_invoice_lines(discount_line.id)
                        invoice_line_ids.append(Command.delete(invoice_line.id))

            if invoice_line_ids:
                vals['invoice_line_ids'] = invoice_line_ids

        return super().write(vals)