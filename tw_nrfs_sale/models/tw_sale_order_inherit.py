# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritSaleOrderNrfs(models.Model):
    _inherit = "tw.sale.order"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    nrfs_id = fields.Many2one('tw.nrfs', string='NRFS Number')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def _get_pricelist(self):
        res = super(InheritSaleOrderNrfs,self)._get_pricelist()
        current_pricelist = False
        if self.nrfs_id and self.division == 'Sparepart':
            current_pricelist = self.company_id.branch_setting_id.pricelist_purchase_sparepart_id
        elif self.nrfs_id and self.division == 'Unit':
            current_pricelist = self.company_id.branch_setting_id.pricelist_purchase_unit_id

        if current_pricelist:
            res = current_pricelist
        return res

    # 13: action methods

    # 14: private methods
    
    