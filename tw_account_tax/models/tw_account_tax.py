# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
# 5: local imports

# 6: Import of unknown third party lib

class InheritAccountTax(models.Model):
    _inherit = "account.tax"
    
    # 7: defaults methods

    # 8: fields
    tax_base_amount = fields.Float('Tax Base Amount', default=1)

    # 9: relation fields
    # company_id = fields.Many2one('res.company', string='Company', required=False, readonly=False, default=False)
    company_id = fields.Many2one('res.company', string="Branch", required=False, readonly=False, default=lambda self: self.env.company.parent_id or self.env.company)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('type_tax_use', 'tax_scope')
    @api.depends_context('append_type_to_tax_name')
    def _compute_display_name(self):
        type_tax_use = dict(self._fields['type_tax_use']._description_selection(self.env))
        for record in self:
            if name := record.name:
                if self._context.get('append_type_to_tax_name'):
                    name += ' (%s)' % type_tax_use.get(record.type_tax_use)
                if len(self.env.companies) > 1 and self.env.context.get('params', {}).get('model') == 'product.template':
                    name += ' (%s)' % record.company_id.display_name
                if record.company_id:
                    if record.country_id != record.company_id._accessible_branches()[:1].account_fiscal_country_id:
                        name += ' (%s)' % record.country_code
            record.display_name = name

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _verify_account_tax(self, untax, tax, tax_use, type):
        """
        return account tax that compatible with tax and untax
        """
        account_taxes = self.sudo().search([
            ('type_tax_use', '=', tax_use),
            ('amount_type', '=', type),
            ('active', '=', True)])
        
        if not account_taxes:
            raise Warning('Account Tax for type tax use %s and type %s does not exist!' % (tax_use, type))

        tax_calculation = round(float(tax)/untax,2)*100
        for record in account_taxes:
            if tax_calculation == record.amount:
                return record

        raise Warning('Account Tax for type tax use %s and type %s, for tax amount %s and untaxed %s does not exist!' % (tax_use, type, tax, untax))
    
    @api.model
    def get_default_sale_tax(self):
        company_id = self.env.user.company_id.id
        tax_ids = self.env['ir.values'].get_default('product.template', 'taxes_id', company_id=company_id)
        return self.browse(tax_ids)