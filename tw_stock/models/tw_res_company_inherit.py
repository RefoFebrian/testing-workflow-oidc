# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritCompany(models.Model):
    _inherit = "res.company"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Warehouse")
    incoming_valuation_on_last_route = fields.Boolean("Valuation on last route", default=True)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        company_obj = super().create(vals_list)
        for company in company_obj:
            self.create_warehouse(company)
        return company_obj

    # 13: action methods

    # 14: private methods
    def create_warehouse(self,company):
        vals = {
            'name': 'WH '+company.name,
            'code': 'WH-'+company.code,
            'partner_id': company.partner_id.id,
            'company_id': company.id,
        }
        
        return self.env['stock.warehouse'].suspend_security().create(vals)
    
