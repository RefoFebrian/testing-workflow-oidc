# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TWActivityDetailBiaya(models.Model):
    _name = "tw.activity.atl.btl.detail.biaya"
    _description = "Detail Biaya Activity"

    # 7: defaults methods

    # 8: fields
    note = fields.Char('Note')
    
    amount = fields.Float('Amount')
    subtotal = fields.Float('Subtotal',compute="_compute_subtotal",readonly=True,store=True)
    tax_amount = fields.Float(string='Tax Amount', digits=(16, 2), compute='_compute_subtotal', store=True)

    state = fields.Selection([
        ('draft','Draft'),
        ('confirmed','Confirmed')], default='draft', string='Status')
    
    is_ppn = fields.Boolean('PPN ?', default=True)
    
    # 9: relation fields
    activity_line_id = fields.Many2one('tw.activity.atl.btl.line', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', 'Vendor')
    tax_id = fields.Many2one('account.tax', string='Taxes')
    submission_type_id = fields.Many2one('tw.selection', string='Submission Type', domain=[('type','=','JenisPengajuan')])
    source_payment_id = fields.Many2one('tw.selection', string='Source Payment', domain=[('type','=','SumberPembayaranBTL')])

    # 10: constraints & sql constraints
    @api.constrains('amount')
    def _check_amount(self):
        for line in self:
            if line.amount < 0:
                raise Warning(_("Amount tidak boleh negatif."))

    # 11: compute/depends & on change methods
    @api.depends('amount', 'tax_id')
    def _compute_subtotal(self):
        for line in self:
            total_exclude = line.amount
            total_included = total_exclude
            tax = 0.0

            currency = line.activity_line_id.company_id.currency_id
            if line.tax_id:
                computed_tax = line.tax_id.compute_all(total_exclude,currency)
                total_included = computed_tax.get('total_included')
                tax = sum([tax['amount'] for tax in computed_tax['taxes']])

            line.tax_amount = tax
            line.subtotal = total_included

    @api.onchange('amount')
    def _onchange_amount(self):
        for line in self:
            if line.amount < 0:
                raise Warning(_("Amount tidak boleh negatif."))

    # 12: override methods

    # 13: action methods

    # 14: private methods
