# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 5: local imports

# 6: Import of unknown third party lib

class InheritProductTemplateAsset(models.Model):
    _inherit = "product.template"
   

    # 7: defaults methods

    # 8: fields
    is_asset = fields.Boolean(string='Is Asset/Prepaid?',default=False)
    is_need_gr = fields.Boolean(string='Need GR?',default=True)

    # 9: relation fields   
    account_asset_ids = fields.Many2many('account.asset.asset',string='Assets')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('sale_ok','asset_category_id')
    def _onchange_sale_ok(self):
        if self.asset_category_id and self.sale_ok:
            self.sale_ok = False
            
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _('You cannot sell an asset product.'),
                }
            }

    # 12: override methods

    # 13: action methods

    # 14: private methods
    