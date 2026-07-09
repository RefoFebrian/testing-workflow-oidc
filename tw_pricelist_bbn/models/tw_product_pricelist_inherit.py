# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwProductPricelist(models.Model):
    _inherit = "product.pricelist"

    # 7: defaults methods
    
    # 8: fields
    type = fields.Selection(selection_add=[('bbn_sales', 'BBN Sales'), ('bbn_purchase', 'BBN Purchase')])

    # 9: relation fields
    plate_id = fields.Many2one(comodel_name='tw.selection', string='Plate', domain=[('type', '=', 'PlateType')])
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Biro Jasa',
        domain=[('category_id.name', '=', 'Birojasa')],
        help="List of Partners that available service for Processing BBN")
    area_id = fields.Many2one(
        comodel_name='res.area', string='Area',
        help="Related branches of the selected Area will be available use this Price List")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('type')
    def _onchange_type(self):
        self.partner_id = False
        self.area_id = False
        self.plate_id = False

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_applicable_rules_domain(self, products, date, **kwargs):
        domain = super()._get_applicable_rules_domain(products, date, **kwargs)
        self and self.ensure_one()
        if self.type == 'bbn_purchase':
            city_id = kwargs.get('city_id')
            domain.append(('city_id', '=', city_id))
        
        return domain
    
    def _get_bbn_sales_pricelist(self, branch, plate):
        if plate.value == 'H':
            pricelist = branch.branch_setting_id.pricelist_sale_bbn_hitam_id
        elif plate.value == 'P':
            pricelist = branch.branch_setting_id.pricelist_sale_bbn_putih_id
        else:
            pricelist =  self.search([('type', '=', 'bbn_sales'),
                                      ('plate_id', '=', plate.id),
                                      ('area_id.company_ids', '=', branch.id)], limit=1)
        if not pricelist:
            raise Warning(_(f"Price List BBN Sales for {plate.name} in {branch.name} not found"))
        return pricelist
    
    def _get_bbn_purchase_pricelist(self, biro_jasa, branch):
        branch_setting = branch.branch_setting_id
        default_birojasa_pl = branch_setting.birojasa_setting_ids.filtered(lambda x: x.default is True)
        pricelist_bbn_purchase = default_birojasa_pl.pricelist_ids.filtered(lambda x: x.active is True)
        if not pricelist_bbn_purchase:
            pricelist_bbn_purchase = self.search([
                ('type', '=', 'bbn_purchase'),
                ('partner_id', '=', biro_jasa.id),
                ('area_id.company_ids', '=', branch.id)])
            if not pricelist_bbn_purchase:
                raise Warning(_(f"Price List BBN Purchase for {biro_jasa.name} in {branch.name} not found"))
        return pricelist_bbn_purchase
    
