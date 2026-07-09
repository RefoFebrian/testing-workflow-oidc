# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    # 7: defaults methods
    
    # 8: fields
    notice_price = fields.Float(string='Notice Price')
    process_price = fields.Float(string='Process Price')
    serv_price = fields.Float(string='Serv Price')
    serv_area_price = fields.Float(string='Serv Area Price')
    capital_fee_price = fields.Float(string='Capital Fee Price')

    # 9: relation fields
    city_id = fields.Many2one('res.city', string='City')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('notice_price', 'process_price', 'serv_price', 'serv_area_price', 'capital_fee_price')
    def _onchange_fixed_price_bbn(self):
        self.fixed_price = self.notice_price + self.process_price + self.serv_price + self.serv_area_price + self.capital_fee_price

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_check_date_constrains_domain(self):
        domain = super()._get_check_date_constrains_domain()
        if self.city_id:
            domain.append(('city_id', '=', self.city_id.id))

        return domain
    
    def _get_check_date_validation_message(self, duplicate_pricelist):
        message = super()._get_check_date_validation_message(duplicate_pricelist)
        return message + f"\nConflicting city: {''.join(duplicate_pricelist.mapped('city_id.name'))}"
        