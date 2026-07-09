# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError
from odoo.tools import groupby

# 5: local imports

# 6: Import of unknown third party lib

class TWAccountDiscount(models.Model):
    _name = "tw.account.discount"
    _description = "Account Discount"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Discount')
    type = fields.Selection(selection=[
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt'),
    ], required=True, help="Transaction that enable to utilize the discount setting.")
    
    discount_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage')
    ], string='Discount Type', default='fixed', required=True,
    help="Type of discount: Fixed Amount or Percentage")
    
    is_all_branch = fields.Boolean(string='Apply to Branches?', help="Apply the discount setting to the childs company (branches).")
    invoice_filter_type_domain = fields.Char(compute='_compute_invoice_filter_type_domain')
    price_include_override = fields.Selection(selection=[('tax_included', 'Tax Included'), ('tax_excluded', 'Tax Excluded')],string='Included in Price',help="Overrides the Company's default on whether the price you use on the product and invoices includes this tax.")

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string="Branch")
    currency_id = fields.Many2one(comodel_name='res.currency', compute='_compute_currency_id')
    tax_country_id = fields.Many2one(
        comodel_name='res.country', compute='_compute_tax_country_id',
        help="used to filter the available taxes depending on the fiscal country and fiscal position.")
    
    # Display name with percentage sign for percentage type
    display_name = fields.Char(compute='_compute_display_name', store=True, index=True)
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal Position',
        check_company=True,
        compute='_compute_fiscal_position_id', store=True, readonly=False, precompute=True,
        ondelete="restrict",
        help="Fiscal positions are used to adapt taxes and accounts for particular "
             "customers or sales orders/invoices. The default value comes from the customer.",
    )
    account_id = fields.Many2one(comodel_name='account.account', string="Account", search=True,
                                 help="COA that will be used in the move entries")
    company_ids = fields.Many2many(comodel_name='res.company', string="Branch", relation='tw_account_discount_company_rel',
                                  column1='discount_id', column2='company_id', domain=[('parent_id', '!=', False)],
                                  compute='_compute_company_ids', store=True)
    tax_ids = fields.Many2many(comodel_name='account.tax',
                               relation='tw_account_discount_tax_rel',
                               column1='discount_id', column2='tax_id')

    # 10: constraints & sql constraints
    _sql_constraints = [('discount_company_uniq',
                         'unique(name, type, company_id)',
                         'Only one discount and type per company is allowed')]
    
    @api.constrains('company_id', 'company_ids')
    def _check_company_ids(self):
        for record in self:
            if record.company_id:
                if record.company_id.id not in record.company_ids.ids:
                    raise ValidationError(_("Company must be included in the Branch."))

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_currency_id(self):
        for record in self:
            record.currency_id = record.company_id.currency_id

    @api.depends('name', 'discount_type')
    def _compute_display_name(self):
        """
        Compute the display name with percentage sign for percentage type discounts
        This will be used globally across all modules
        """
        for record in self:
            if record.discount_type == 'percentage' and record.name:
                record.display_name = f"{record.name} (%)"
            else:
                record.display_name = record.name

    @api.depends('is_all_branch', 'company_id')
    def _compute_company_ids(self):
        for record in self:
            if record.is_all_branch:
                if record.company_id:
                    record.company_ids = (record.company_id.child_ids + record.company_id).mapped('id')
                else:
                    record.company_ids = False

    # these computes is a copy from account.move models to create domain filter for taxes
    @api.depends('type')
    def _compute_invoice_filter_type_domain(self):
        for record in self:
            if record.type in ['out_invoice', 'out_refund', 'out_receipt']:
                record.invoice_filter_type_domain = 'sale'
            elif record.type in ['in_invoice', 'in_refund', 'in_receipt']:
                record.invoice_filter_type_domain = 'purchase'
            else:
                record.invoice_filter_type_domain = False

    @api.depends('company_id.account_fiscal_country_id', 'fiscal_position_id', 'fiscal_position_id.country_id', 'fiscal_position_id.foreign_vat')
    def _compute_tax_country_id(self):
        foreign_vat_records = self.filtered(lambda r: r.fiscal_position_id.foreign_vat)
        for fiscal_position_id, record_group in groupby(foreign_vat_records, key=lambda r: r.fiscal_position_id):
            self.env['tw.account.discount'].concat(*record_group).tax_country_id = fiscal_position_id.country_id
        for company_id, record_group in groupby((self-foreign_vat_records), key=lambda r: r.company_id):
            self.env['tw.account.discount'].concat(*record_group).tax_country_id = company_id.account_fiscal_country_id

    @api.depends('company_id')
    def _compute_fiscal_position_id(self):
        for record in self:
            partner = record.company_id.partner_id
            record.fiscal_position_id = self.env['account.fiscal.position'].with_company(record.company_id)._get_fiscal_position(partner)

    @api.onchange('price_include_override')
    def _onchange_price_include_override(self):
        self.tax_ids = False

    # 13: action methods

    # 14: private methods
    def _get_discount_account(self, branch_obj, type):
        discount_account = self.suspend_security().search([('type', '=', type),'|', ('is_all_branch', '=', True), ('company_ids', 'in', branch_obj.id)])
        return discount_account
    
    def _prepare_discount_invoice_line(self, amount, company_id=False, tax_ids=False):
        self.ensure_one()
        
        tax_vals = []
        tax_ids = tax_ids or self.tax_ids.ids
        if tax_ids:
            tax_vals = [(6, 0, tax_ids)]

        if not self.account_id:
            raise ValidationError(_("Account untuk Account Discount %s belum disetting, silahkan konfigurasi terlebih dahulu." % self.name))
        res = {
            'name': self.name,
            'account_id': self.account_id.id,
            'currency_id': self.currency_id.id,
            'discount_id': self.id,
            'amount': amount,
            'company_id': company_id or self.company_id.id,
            'tax_ids': tax_vals,
        }
        return res