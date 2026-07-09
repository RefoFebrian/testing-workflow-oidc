# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class LeadAddresses(models.Model):
    _name = "tw.lead.addresses"
    _description = "Lead Addresses"

    # 7: defaults methods
    def _get_default_country(self):
        return self.env.ref('base.id').id
    
    # 8: fields
    name = fields.Char('Address Name')
    rt = fields.Char('RT', store=True)
    rw = fields.Char('RW', store=True)
    street = fields.Char('Street', store=True)
    street2 = fields.Char('Street2', store=True)
    zip = fields.Char('Zip', change_default=True)
    sub_district = fields.Char('Sub District')
    district = fields.Char('District Name')
    city = fields.Char('City Name')
    state = fields.Char('Province Name')
    address_type = fields.Char(related='address_type_id.value', store=True)
    
    is_same_ktp = fields.Boolean('Sesuai alamat KTP?', default=False)
    
    # 9: relation fields
    lead_id = fields.Many2one('tw.lead')
    address_type_id = fields.Many2one(comodel_name='tw.selection', string="Address Type", domain="[('type', '=', 'AddressType')]")
    sub_district_id = fields.Many2one(comodel_name='res.sub.district', string="Sub-district",
                                      store=True, domain="[('district_id', '=', district_id)]", help='')
    district_id = fields.Many2one(comodel_name='res.district', string="District",
                                  store=True, domain="[('city_id', '=', city_id)]", help='')
    city_id = fields.Many2one(comodel_name='res.city', string="City",
                              store=True, domain="[('state_id', '=', state_id)]", help='')
    state_id = fields.Many2one('res.country.state', string="Province",
                               store=True, domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string="Country", store=True, default=_get_default_country)     
    
    # 10: constraints & sql constraints
    @api.constrains('address_type', 'lead_id')
    def _check_single_ktp_address(self):
        """
        Constraint to ensure only one KTP address per lead.
        """
        for record in self:
            if record.address_type == 'ktp':
                ktp_address = record.search([
                    ('lead_id', '=', record.lead_id.id),
                    ('address_type', '=', 'ktp'),
                    ('id', '!=', record.id)  # Exclude current record when updating
                ], limit=1)
                if ktp_address:
                    raise Warning("Only one KTP address is allowed per lead.")
    

    # 11: compute/depends & on change methods

    @api.onchange('sub_district_id')
    def _onchange_sub_district(self):
        self.zip = False
        if self.sub_district_id:
            self.zip = self.sub_district_id.zip_code

    @api.onchange('district_id')
    def _onchange_district_id(self):
        self.sub_district_id = False
        self.zip = False

    @api.onchange('city_id')
    def _onchange_city_id(self):
        self.district_id = False

    @api.onchange('state_id')
    def _onchange_state_id(self):
        self.city_id = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        address = super().create(vals_list)
        for addr in address:
            if not addr.name:
                identification_number = addr.lead_id.identification_number
                address_type = addr.address_type_id.name
                addr.name = f'{identification_number} - {address_type}'
        
        return address

    # 13: action methods

    # 14: private methods
