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


class InheritPartnerCustomer(models.Model):
    _inherit = "res.partner"

    whatsapp = fields.Char(string='Whatsapp')
    ethnic_group = fields.Char(string='Suku')
    job_position = fields.Char(string='Jabatan')

    responsible_occupation_id = fields.Many2one('tw.selection', string='Pekerjaan Penanggung Jawab' , domain=[('type','=','Occupation')])
    customer_type_id = fields.Many2one('tw.selection',string='Jenis Customer', domain=[('type','=','CustomerType')])


    cdb_partner_ids = fields.One2many('tw.partner.cdb', 'partner_id', string='CDB Data')

    def sync_partner_to_cdb(self, **kwargs):
        """
        Sync data from res.partner to tw.partner.cdb
        
        :param dict kwargs: Additional fields to include in the CDB record
                        Example: lot_ids, company_id, etc.
        :return: Created or updated CDB record
        """
        cdb_model = self.env['tw.partner.cdb']
        for partner in self:
            # Base values from partner
            cdb_vals = {
                'partner_id': partner.id,
                'name': partner.name,
                'identification_number': partner.identification_number,
                'identification_family_number': partner.identification_family_number,
                'birthplace': partner.birthplace,
                'birthdate': partner.birthdate,
                'mobile': partner.mobile,
                'email': partner.email,
                'whatsapp': partner.whatsapp,
                'phone': partner.phone,
                'street': partner.street,
                'street2': partner.street2,
                'street_domicile': partner.street_domicile,
                'street2_domicile': partner.street2_domicile,
                'rt': partner.rt,
                'rw': partner.rw,
                'rt_domicile': partner.rt_domicile,
                'rw_domicile': partner.rw_domicile,
                'zip_code': partner.zip,
                'zip_code_domicile': partner.zip_domicile,
                'responsible': partner.responsible,
                'ethnic_group': partner.ethnic_group,
                'job_position': partner.job_position,
                'state_text': partner.state_text,
                'city_text': partner.city_text,
                'district_text': partner.district_text,
                'sub_district_text': partner.sub_district_text,
                'date': fields.Date.today(),
            }
            
            # Add company_id from kwargs if provided, otherwise from partner
            cdb_vals['company_id'] = kwargs.pop('company_id', partner.company_id.id)
            
            # Get all valid fields from the CDB model
            valid_fields = set(cdb_model._fields.keys())
            
            # Add only valid fields from kwargs
            for field, value in kwargs.items():
                if field in valid_fields:
                    cdb_vals[field] = value
            
            # Handle related fields
            related_fields = [
                'gender_id', 'religion_id', 'education_id', 'occupation_id',
                'responsible_occupation_id', 'hobby_id', 'blood_type_id',
                'state_id', 'city_id', 'district_id', 'sub_district_id', 'country_id',
                'state_domicile_id', 'city_domicile_id', 'district_domicile_id', 'sub_district_domicile_id',
                'customer_code_id', 'customer_type_id', 'housing_tenure_id',
                'mobile_plan_status_id', 'expense_id', 'unit_usage_id',
                'unit_operator_id', 'motor_brand_id', 'motor_type_id'
            ]
            
            # Only add related fields that exist on the partner and aren't in cdb_vals
            for field in related_fields:
                if field not in cdb_vals and hasattr(partner, field) and partner[field]:
                    cdb_vals[field] = partner[field].id
                    
            return cdb_model.suspend_security().create(cdb_vals)