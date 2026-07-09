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


class TWBranchSetting(models.Model):
    _inherit = "tw.branch.setting"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    pricelist_sale_bbn_hitam_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist Sale BBN Hitam',
        domain=[('type', '=', 'bbn_sales'),('plate_id.value','=','H')])
    pricelist_sale_bbn_putih_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist Sale BBN Putih',
        domain=[('type', '=', 'bbn_sales'),('plate_id.value','=','P')])
    pricelist_sale_bbn_merah_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist Sale BBN Merah',
        domain=[('type', '=', 'bbn_sales'),('plate_id.value','=','M')])
    birojasa_setting_ids = fields.One2many(
        comodel_name='tw.branch.setting.birojasa',
        inverse_name='branch_setting_id',
        string='Birojasa Settings',
        help="List of Birojasa settings for this branch. Each setting can have its own pricelists."
    )

    # 10: constraints & sql constraints
    @api.constrains('birojasa_setting_ids')
    def _check_birojasa_default(self):
        for branch in self:
            default_birojasa = branch.birojasa_setting_ids.filtered(lambda b: b.default)
            if len(default_birojasa) > 1:
                raise Warning(_("Only one Biro Jasa can be set as default per branch. Please review the settings."))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
