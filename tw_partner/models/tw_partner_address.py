# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class TwPartnerAddress(models.Model):
    _name = "tw.partner.address"
    _description = "Partner Address"

    # 7: defaults methods
    
    # 8: fields
    name = fields.Char('Address Name')
    rt = fields.Char('RT', store=True)
    rw = fields.Char('RW', store=True)
    street = fields.Char('Street', store=True)
    street2 = fields.Char('Street2', store=True)
    zip = fields.Char('Zip', change_default=True)
    sub_district = fields.Char('Sub district name')
    district = fields.Char('District name')
    city = fields.Char('City name')
    state = fields.Char('Province name')

    is_main_address = fields.Boolean('Is Main Address', default=False)

    # 9: relation fields
    partner_id = fields.Many2one('res.partner')
    address_type_id = fields.Many2one(comodel_name='tw.selection', domain="[('type', '=', 'AddressType')]")
    sub_district_id = fields.Many2one(comodel_name='res.sub.district', string="Sub-district", store=True, domain="[('district_id', '=', district_id)]", help='')
    district_id = fields.Many2one(comodel_name='res.district', string="District", store=True, domain="[('city_id', '=', city_id)]", help='')
    city_id = fields.Many2one(comodel_name='res.city', string="City", store=True, domain="[('state_id', '=', state_id)]", help='')
    state_id = fields.Many2one('res.country.state', string="Province", store=True, domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string="Country", store=True)      

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('sub_district_id')
    def _onchange_sub_district_id(self):
        for address in self:
            address.sub_district = address.sub_district_id.name
            address.zip = address.sub_district_id.zip_code
            address.district_id = address.sub_district_id.district_id.id
            address.district = address.sub_district_id.district_id.name
            address.city_id = address.sub_district_id.district_id.city_id.id
            address.city = address.sub_district_id.district_id.city_id.name
            address.state_id = address.sub_district_id.district_id.city_id.state_id.id
            address.state = address.sub_district_id.district_id.city_id.state_id.name
            address.country_id = address.sub_district_id.district_id.city_id.state_id.country_id.id

    @api.onchange('district_id')
    def _onchange_district_id(self):
        for address in self:
            address.district = address.district_id.name
            address.city_id = address.district_id.city_id.id
            address.city = address.district_id.city_id.name
            address.state_id = address.district_id.city_id.state_id.id
            address.state = address.district_id.city_id.state_id.name
            address.country_id = address.district_id.city_id.state_id.country_id.id

    @api.onchange('city_id')
    def _onchange_city_id(self):
        for address in self:
            address.city = address.city_id.name
            address.state_id = address.city_id.state_id.id
            address.state = address.city_id.state_id.name
            address.country_id = address.city_id.state_id.country_id.id

    @api.onchange('state_id')
    def _onchange_state_id(self):
        for address in self:
            address.state = address.state_id.name
            address.country_id = address.city_id.state_id.country_id.id

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        address = super().create(vals_list)
        for addr in address:
            if not addr.name:
                identification_number = addr.partner_id.identification_number
                address_type = addr.address_type_id.name
                addr.name = f'{identification_number} - {address_type}'
        
        return address

    # 13: action methods

    # 14: private methods