# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, SUPERUSER_ID, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritProductCategory(models.Model):
    _inherit = "product.category"

    # 7: defaults methods

    # 8: fields
    cost_method_template = fields.Selection(
        selection=[('fifo', 'FIFO'),
                   ('average', 'Average'),
                   ('standard', 'Standard Price')],
        string='Cost Method Template',
        help="Global policy for this category; auto-applied to all companies."
    )
    property_valuation = fields.Selection([
        ('manual_periodic', 'Manual'),
        ('real_time', 'Automated')], string='Inventory Valuation',
        company_dependent=True, copy=True,
        default='real_time',
        help="""Manual: The accounting entries to value the inventory are not posted automatically.
        Automated: An accounting entry is automatically created to value the inventory when a product enters or leaves the company.
        """)
    # Inherit property valuation & cost method so it will be the same each company

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('cost_method_template')
    def onchange_cost_method_template(self):
        if self.cost_method_template:
            self.property_cost_method = self.cost_method_template

    def _get_accounting_sync_field_names(self):
        return (
            'property_cost_method',
            'property_valuation',
            'property_stock_valuation_account_id',
            'property_stock_account_input_categ_id',
            'property_stock_account_output_categ_id',
            'property_stock_journal',
            'property_account_income_categ_id',
            'property_account_expense_categ_id',
            'property_account_creditor_price_difference_categ',
            'property_account_downpayment_categ_id',
        )

    # 12: override methods
    # TODO: Error on first install
    # def _register_hook(self):
    #     res = super()._register_hook()
    #     cats = self.env['product.category'].search([('cost_method_template', '!=', False)])
    #     if cats:
    #         cats._sync_cost_method()
    #     return res
        
    @api.model_create_multi
    def create(self,vals_list):
        recs = super().create(vals_list)
        recs._sync_accounting_data()
        return recs

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})

        for field_name in self._get_accounting_sync_field_names():
            if field_name not in self._fields:
                continue
            if field_name not in default and self[field_name]:
                default[field_name] = self[field_name].id if self._fields[field_name].type == 'many2one' else self[field_name]

        return super().copy(default)

    def write(self, vals):
        res = super().write(vals)
        # Only resync when template changes and the change is not from sync method
        if not self.env.context.get('skip_accounting_sync', False):
            if any(field_name in vals for field_name in self._get_accounting_sync_field_names() if field_name in self._fields):
                self._sync_accounting_data()
        return res
    
    def action_sync_accounting_data(self):
        self._sync_accounting_data()

    # 14: private method
    def _sync_accounting_data(self, companies=None):
        """Apply cost_method_template to the company-dependent cost_method slot
           for each company in 'companies' (or all companies if None)."""
        if not self:
            return
            
        if companies is None:
            companies = self.env['res.company'].sudo().search([])

        for categ in self:
            vals = {}
            for field_name in self._get_accounting_sync_field_names():
                if field_name not in categ._fields:
                    continue
                field = categ._fields[field_name]
                value = categ[field_name]
                if not value:
                    continue
                vals[field_name] = value.id if field.type == 'many2one' else value
            if vals:
                # Write data per company
                for company in companies:
                    vals_write = vals.copy()
                    # Jika sudah sama, tidak perlu di write karena akan muncul warning "You cannot change the costing method of product valuated by lot/serial number."
                    if vals_write.get('property_cost_method'):
                        if categ.with_company(company).property_cost_method == categ.cost_method_template:
                            vals_write.pop('property_cost_method')
                    if vals_write.get('property_valuation'):
                        if categ.with_company(company).property_valuation == categ.property_valuation:
                            vals_write.pop('property_valuation')
                    categ.with_company(company).with_context(skip_accounting_sync=True).write(vals_write)

    def sync_field_based_on_company(self, company_code='H2Z', categ_domain=[('parent_id','!=',False)]):
        """Sync field of all_categ based on company_code."""
        company = self.env['res.company'].search([('code','=',company_code)],limit=1)
        all_categ = self.env['product.category'].search(categ_domain)
        for categ in all_categ:
            categ.with_company(company)._sync_accounting_data()
            