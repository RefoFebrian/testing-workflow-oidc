# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
_logger = logging.getLogger(__name__)

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, exceptions, _

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    service_category_id = fields.Many2one(comodel_name='tw.selection', string='Service Category' , domain=[('type','=','PricelistServiceCategory')], help="Field that can be used if the product (Unit) has a service category.")
    cost_based_on_id = fields.Many2one(comodel_name='tw.selection', string='Cost Based On' , domain=[('type','=','PricelistCategory')], help="Pricelist that can be used for expeditions, if necessary.")
    pricelist_version_id = fields.Many2one('tw.product.pricelist.version', string="Price List Version", ondelete='cascade')
    pricelist_type = fields.Selection(related='pricelist_version_id.pricelist_id.type', string='Pricelist Type', store=False)

    # 10: constraints & sql constraints
    @api.constrains('cost_based_on_id', 'pricelist_version_id')
    def _check_cost_based_on_expedition(self):
        """Validate cost_based_on_id is mandatory for expedition pricelist type."""
        for rec in self:
            if rec.pricelist_type == 'expedition' and not rec.cost_based_on_id:
                raise exceptions.ValidationError(
                    _("'Cost Based On' is required for Expedition pricelist type.")
                )

    @api.constrains('date_start', 'date_end','product_tmpl_id', 'pricelist_version_id','service_category_id')
    def _check_date(self):
        for supplierinfo in self:
            # Prepare domain to check overlapping pricelist versions
            domain = [
                ('pricelist_version_id', '=', supplierinfo.pricelist_version_id.id),
                ('id', '!=', supplierinfo.id),
                ('pricelist_version_id', '!=', False),
                ('product_tmpl_id', '=', supplierinfo.product_tmpl_id.id),
                ('product_id', '=', supplierinfo.product_id.id),
                ('service_category_id', '=', supplierinfo.service_category_id.id),
                ('cost_based_on_id', '=', supplierinfo.cost_based_on_id.id),
                '|', ('date_end', '=', False), ('date_end', '>=', supplierinfo.date_start),
                '|', ('date_start', '=', False), ('date_start', '<=', supplierinfo.date_end),
            ]

            # Search for overlapping pricelist versions
            overlapping_versions = self.search(domain)            
            if overlapping_versions:               
                raise exceptions.ValidationError(
                    'You cannot have two pricelist versions that overlap! '
                    f'Conflicting versions [Supplier]: {", ".join(overlapping_versions.mapped("product_name"))}'
                )

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods