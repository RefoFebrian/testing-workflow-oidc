# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
import logging
_logger = logging.getLogger(__name__)

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, exceptions, _

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError, RedirectWarning

# 5: local imports

# 6: Import of unknown third party lib

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    # 7: defaults methods

    # 8: fields
    type = fields.Selection([('sales', 'Sales'), ('purchase', 'Purchase'),], string="Pricelist Type", default='sales')
    is_pricelist_version_active = fields.Boolean(string="Is Pricelist Version Active", help="If checked, the pricelist version will be active and can be used for pricing.", compute="_compute_is_pricelist_version_active")

    # 9: relation fields
    version_ids = fields.One2many('tw.product.pricelist.version', 'pricelist_id', string="Version")

    # 10: constraints & sql constraints
    def unlink(self):
        for pricelist in self:
            if pricelist.version_ids:
                raise ValidationError(_("You cannot delete a pricelist with versions."))
        return super(ProductPricelist, self).unlink()

    # 11: compute/depends & on change methods

    def _compute_is_pricelist_version_active(self):
        for pricelist in self:
            pricelist.is_pricelist_version_active = any(version.state == 'confirmed' for version in pricelist.version_ids)

    # 12: override methods

    # 13: action methods
    def action_upload_pricelist_version(self):
        domain = []
        name = 'Upload Pricelist Version'
        path = 'upload-tw-pricelist-version'

        form_view_id = self.env.ref('tw_pricelist.tw_upload_pricelist_version_view_wizard').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.upload.pricelist.version',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'pricelist_id': self.id,
                'company_id': self.company_id.id,
                'readonly_by_pass': 1,
                'type': self.type
            },
        }

    # 14: private methods

    # Category service pricelist (category_service = service_category_id)
    def _price_get_by_category_service(self, product, quantity, category_service): 
        price_dict = self._price_get(product, quantity, category_service=category_service)
        return price_dict
    
    # Expedition pricelist (category_price = cost_based_on_id)
    def _price_get_by_category_price(self, product, quantity, category_price):             
        price_dict = self._price_get(product, quantity, category_price=category_price)
        return price_dict
    
    # Additional domain for pricelist item
    def _get_applicable_rules_domain(self, products, date, **kwargs):
        domain = super()._get_applicable_rules_domain(products, date, **kwargs)
        domain += [('state', '=', 'active')]
        domain += [('pricelist_version_id.state', '=', 'confirmed')]
        # Category Service Domain
        if kwargs.get('category_service', False):
            domain = [('service_category_id', '=', kwargs.get('category_service', False))] + domain
        # Expedition Service Domain
        if kwargs.get('category_price', False):
            domain = [('cost_based_on_id', '=', kwargs.get('category_price', False))] + domain
        # Area Domain
        if kwargs.get('company_id', False):
            areas = self.env['res.area'].search([('company_ids', 'in', [kwargs.get('company_id', False)])])
            product_version = self.env['tw.product.pricelist.version'].search([('pricelist_id', '=', self.id), ('area_id', 'in', areas.ids)])
            if product_version:
                domain = [('area_id', 'in', areas.ids)] + domain
            else:
                domain = ['|', ('area_id', '=', False), ('area_id', '=', None)] + domain
        return domain
    
    def _get_applicable_rules(self, products, date, **kwargs):
        self and self.ensure_one()  # self is at most one record
        domain = self._get_applicable_rules_domain(products, date, **kwargs)
        product_pricelist_item = super(ProductPricelist,self)._get_applicable_rules(products, date, **kwargs)
        if products:  
            if not product_pricelist_item and products.categ_id.is_only_use_pricelist:
                warning = "Product Pricelist Item not found for this product '%s'. \nPricelist Name: '%s' \nPricelist Type: '%s'" % (products.display_name, self.name, self.type)
                if kwargs.get('city_id'):
                    city_obj = self.env['res.city'].suspend_security().search([('id', '=', kwargs.get('city_id'))])
                    warning += "\nCity: '%s'" % (city_obj.name)
                if kwargs.get('category_service'):
                    category_service_obj = self.env['tw.selection'].suspend_security().search([('id', '=', kwargs.get('category_service'))])
                    warning += "\nCategory Service: '%s'" % (category_service_obj.name)
                if kwargs.get('category_price'):
                    category_price_obj = self.env['tw.selection'].suspend_security().search([('id', '=', kwargs.get('category_price'))])
                    warning += "\nCategory Price: '%s'" % (category_price_obj.name)
                
                if self.id:
                    form_view = self.env.ref('tw_pricelist_form_view', raise_if_not_found=False)
                    action = {
                        'res_model': 'product.pricelist',
                        'res_id': self.id,
                        'type': 'ir.actions.act_window',
                        'domain': domain,
                        'target': 'new',
                        'views': [(form_view and form_view.id, 'form')]
                    }
                    raise RedirectWarning(warning, action, button_text="Go to Pricelist")
                else:
                    raise Warning(warning)

        return product_pricelist_item