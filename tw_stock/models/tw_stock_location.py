# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockLocation(models.Model):
    _inherit = "stock.location"
    _description = "Stock Location"
    _rec_names_search = ['name', 'complete_name', 'description']
    
    # 7: defaults methods

    # 8: fields
    description = fields.Char(string="Description")
    is_temporary_location = fields.Boolean(string="Temporary Location")
    is_allow_negative_stock = fields.Boolean(
        string="Allow Negative Stock",
        default=False,
        help="If checked, stock operations can cause negative stock levels at this location. "
             "This allows validating pickings even when there's insufficient stock, "
             "resulting in negative quants."
    )
    is_restrict_capacity = fields.Boolean(string="Restrict Capacity")
    capacity = fields.Integer(string="Capacity")
    residual_capacity = fields.Integer(string="Residual Capacity", compute='_compute_taken_capacity', store=True)
    taken_capacity = fields.Float(string="Taken Capacity", compute='_compute_taken_capacity', store=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    district = fields.Char(string='Kecamatan')
    sub_district = fields.Char(string='Kelurahan')
    rt = fields.Char(string='RT', size=3)
    rw = fields.Char(string='RW', size=3)

    # 9: relation fields
    company_id = fields.Many2one("res.company", string="Branch")
    type_id = fields.Many2one('tw.selection', "Type", domain=[('type', '=', 'StockLocation')])
    state_id = fields.Many2one(comodel_name='res.country.state', string='Provinsi')
    city_id = fields.Many2one(comodel_name='res.city', string='Kabupaten', domain="[('state_id', '=', state_id)]")
    district_id = fields.Many2one(comodel_name='res.district', string='Kecamatan', domain="[('city_id', '=', city_id)]")
    sub_district_id = fields.Many2one(comodel_name='res.sub.district', string='Kelurahan', domain="[('district_id', '=', district_id)]")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('state_id')
    def _onchange_province(self):
        if self.state_id:
            return {
                'domain': {'city_id': [('state_id', '=', self.state_id.id)]},
                'value': {'city_id': False}
            }
        return {
            'domain': {'city_id': [('state_id', '=', False)]},
            'value': {'city_id': False}
        }

    @api.onchange('city_id')
    def _onchange_city(self):
        if self.city_id:
            return {
                'domain': {'district_id': [('city_id', '=', self.city_id.id)]},
                'value': {'district_id': False}
            }
        return {
            'domain': {'district_id': [('city_id', '=', False)]},
            'value': {'district_id': False}
        }

    @api.onchange('district_id')
    def _onchange_kecamatan(self):
        if self.district_id:
            return {
                'domain': {'sub_district_id': [('district_id', '=', self.district_id.id)]},
                'value': {'district': self.district_id.name, 'sub_district_id': False}
            }
        return {
            'domain': {'sub_district_id': [('district_id', '=', False)]},
            'value': {'sub_district_id': False}
        }
    
    @api.onchange('sub_district_id')
    def _onchange_kelurahan(self):
        if self.sub_district_id:
            return {
                'value': {'sub_district': self.sub_district_id.name}
            }
    
    def _get_allow_negative_stock(self):
        """
        Get the allow_negative_stock setting from the root/warehouse location.
        Child locations inherit this setting from their parent.
        
        Traverses up the location hierarchy to find the root location
        (the one without a parent) and returns its is_allow_negative_stock value.
        """
        self.ensure_one()
        location = self
        # Traverse up to find root location (warehouse level)
        while location.location_id:
            location = location.location_id
        return location.is_allow_negative_stock

    @api.depends('capacity', 'quant_ids')
    def _compute_taken_capacity(self):
        for record in self:
            record.residual_capacity = 0
            record.taken_capacity = 0
            if record.capacity:
                record.taken_capacity = 100.0 * len(record.quant_ids) / record.capacity
                record.residual_capacity = record.capacity - len(record.quant_ids)

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('is_restrict_capacity') == True:
                if vals.get('capacity') <= 0:
                    raise ValidationError(_("The capacity of location cannot be 0 or less than 0"))
        return super(InheritStockLocation, self).create(vals_list)
    
    def write(self,vals):
        is_restrict_capacity = vals.get('is_restrict_capacity')
        if is_restrict_capacity == True:
            capacity = vals.get('capacity',self.capacity)
            if capacity <= 0:
                raise ValidationError(_("The capacity of location cannot be 0 or less than 0"))
        return super(InheritStockLocation, self).write(vals)

    # 13: action methods

    # 14: private methods
    def _create_location(self,**kwargs):
        """Inherit this metode to Create Location"""
        vals = self._prepare_create_location()
        
        type_id = kwargs.get('type_id')
        name = kwargs.get('name')
        usage = kwargs.get('usage') or 'internal'

        vals.update({
            'type_id':type_id if type_id else False,
            'name':name,
            'usage':usage,
        })
 
        return self.create(vals)
    
    def _prepare_create_location(self):
        return {
            'company_id':self.company_id.id,    
            'name':self.name,        
            'usage':'internal',
            'active':True,
            'description':self.name,
            'type_id':self.type_id.id if self.type_id else False,
        }
