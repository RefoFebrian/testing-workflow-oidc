# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class TWAccountMoveDiscount(models.Model):
    _name = "account.move.discount"
    _description = "Journal Entry Discount"
    
    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name', related='discount_id.name', store=True)
    amount = fields.Float(string='Amount')

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(comodel_name='res.currency', compute='_compute_currency_id')
    move_id = fields.Many2one(comodel_name='account.move', string='Journal Entry')
    discount_id = fields.Many2one(comodel_name='tw.account.discount', string='Discount')
    account_id = fields.Many2one(comodel_name='account.account', related='discount_id.account_id')
    tax_ids = fields.Many2many(comodel_name='account.tax', relation='account_move_discount_tax_rel',
                               column1='discount_id', column2='tax_id')

    # 10: constraints & sql constraints
    sql_constraints = [('account_discount_uniq',
                        'unique(discount_id, move_id)',
                        "Similar discount can not be more than one!")]
    
    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError(_("The amount must be greater than 0."))

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_currency_id(self):
        for record in self:
            record.currency_id = record.company_id.currency_id

    # 12: override methods

    # 13: action methods

    # 14: private method
    def _prepare_discount_invoice_line(self, vals):
        discount_id = self.env['tw.account.discount'].browse(vals.get('discount_id'))
        return (Command.create({
            'company_id': vals.get('company_id'),
            'discount_id': discount_id.id,
            'display_type': 'product',
            'name': discount_id.name,
            'price_unit': -vals.get('amount'),
            'tax_ids': vals.get('tax_ids'),
            'account_id': discount_id.account_id.id
        }))
    
    def _get_related_invoice_lines(self, discount_id):
        discount_line = self.browse(discount_id)
        invoice_line = self.env['account.move.line'].search([
            ('move_id', '=', discount_line.move_id.id),
            ('account_id', '=', discount_line.account_id.id),
            ('name', '=', discount_line.name)
        ])
        return invoice_line