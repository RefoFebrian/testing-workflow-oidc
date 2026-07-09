# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning


class PilotProject(models.Model):
    _name = "tw.pilot.project"
    _description = "Pilot Project"

    name = fields.Char('Name')
    company_id_result = fields.Char(string='Result Branch')
    
    description = fields.Text('Description')
    
    active = fields.Boolean(default=False, string='Active?')
    is_using_rule = fields.Boolean('Using Rule?', default=False)

    output_type_id = fields.Many2one(comodel_name='tw.selection', string='Output Type' , domain=[('type','=','OutputType')])
    model_id = fields.Many2one('ir.model', string='Model Pilot')
    company_ids = fields.Many2many("res.company", "pilot_project_company_rel", 'company_id', 'pilot_id', string="Branch", domain="[('parent_id', '!=', False)]")

    @api.model_create_multi
    def create(self,vals_list):
        record = super(PilotProject, self).create(vals_list)
        record.generate_company_id_result()
        record.action_activate()
        return record
    
    def write(self, vals):
        if self.active and self.is_using_rule and vals.get('active', True) is not False and any(field in vals for field in self._fields):
            raise Warning("Tidak dapat mengedit Pilot Project yang sedang aktif. Nonaktifkan terlebih dahulu.")
        
        write = super(PilotProject, self).write(vals)
        if vals.get('output_type_id'):
            self.generate_company_id_result()
        return write

    def action_activate(self):
        if self.active:
            raise Warning("Pilot Project sudah aktif. Nonaktifkan terlebih dahulu untuk melakukan perubahan.")
        
        # Set active to True
        self.active = True
        if self.is_using_rule:
            # Cek atau buat IR Rule
            domain = [('company_id', 'in', self.company_ids.ids)]
            existing_rule = self.env['ir.rule'].search([('model_id', '=', self.model_id.id), ('name', '=', self.name)])
            if existing_rule:
                # Update rule jika sudah ada
                existing_rule.write({
                    'domain_force': str(domain),
                    'active': True
                })
            else:
                # Buat rule baru jika belum ada
                self.env['ir.rule'].sudo().create({
                    'name': self.name,
                    'model_id': self.model_id.id,
                    'domain_force': str(domain),
                    'active': True,
                })

    def action_deactivate(self):
        if not self.active:
            raise Warning("Pilot Project sudah nonaktif.")
        
        # Set active to False
        self.active = False

        if self.is_using_rule:
            # Nonaktifkan IR Rule
            existing_rule = self.env['ir.rule'].search([('model_id', '=', self.model_id.id), ('name', '=', self.name)])

            if existing_rule:
                existing_rule.write({'active': False})

    def generate_company_id_result(self):
        if self.output_type_id:
            result = eval( self.output_type_id.value % ( self.company_ids.ids ) )
            self.company_id_result = str(result)