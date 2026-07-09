# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class ResBranch(models.Model):
    _inherit = "tw.branch.setting"


    # 9: relation fields
    pricelist_purchase_unit_id = fields.Many2one('product.pricelist', string="Price List Beli Unit", ondelete='cascade', domain=[('type','=','purchase'),('active','=',True)])
    pricelist_purchase_sparepart_id = fields.Many2one('product.pricelist', string="Price List Beli Sparepart", ondelete='cascade', domain=[('type','=','purchase'),('active','=',True)])
    pricelist_sale_unit_id = fields.Many2one('product.pricelist', string="Price List Jual Unit", ondelete='cascade', domain=[('type','=','sales'),('active','=',True)])
    pricelist_sale_sparepart_id = fields.Many2one('product.pricelist', string="Price List Jual Sparepart", ondelete='cascade', domain=[('type','=','sales')])
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    
    # 12: override methods

    # 13: action methods
    
    # 14: private methods
    def _get_pricelist_purchase(self,branch,division):
        pricelist = self.env['product.pricelist']
        if not branch:
            raise Warning("Silahkan pilih Cabang terlebih dahulu")
        if not division:
            raise Warning("Silahkan pilih Division terlebih dahulu")
        branch_settings = self.search([('company_id','=',branch.id)])
        if division == 'Unit':
            pricelist = branch_settings.pricelist_purchase_unit_id
            if pricelist.active == False:
                branch_settings.pricelist_purchase_unit_id = False
        elif division == 'Sparepart':
            pricelist = branch_settings.pricelist_purchase_sparepart_id
            if pricelist.active == False:
                branch_settings.pricelist_purchase_sparepart_id = False
        return pricelist

