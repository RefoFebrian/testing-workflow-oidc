from odoo import models, fields, api, Command
from odoo.exceptions import UserError as Warning

class EmployeeArea(models.Model):
    _inherit = "hr.employee"

    area_id = fields.Many2one('res.area', string='Area')
    available_area_ids = fields.Many2many('res.area', string='Available Area', compute='_compute_available_area_ids')

    @api.depends('company_id')    
    def _compute_available_area_ids(self):
        self.available_area_ids = False
        for record in self:
            if record.company_id:
                record.available_area_ids = self.env['res.area'].sudo().search([('company_ids', 'in', record.company_id.id)])
    
    @api.onchange('company_id')
    def _onchange_company_job_id(self):
        onchange = super()._onchange_company_job_id()
        self.area_id = False
        return onchange

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        return records
    
    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in ['area_id', 'is_user', 'company_id']):
            for record in self:
                user = record.user_id
                if user:
                    area = record.area_id
                    if not area:
                        continue
                    
                    allowed_company_ids = area.company_ids.ids
                    if record.company_id.id not in allowed_company_ids:
                        raise Warning('Company %s is not suitable in area %s.' % (record.company_id.name, area.name))
                    
                    # Only write if there's a meaningful change to avoid redundant flushes
                    if user.area_id != area or user.company_id != record.company_id or set(user.company_ids.ids) != set(allowed_company_ids):
                        user.sudo().write({
                            'area_id': area.id,
                            'company_ids': [Command.set(allowed_company_ids)],
                            'company_id': record.company_id.id,
                        })
        
        return res

    def _get_user_vals(self, **kwargs):
        vals = super()._get_user_vals(**kwargs)
        if self.area_id:
            allowed_company_ids = self.area_id.company_ids.ids
            if self.company_id.id not in allowed_company_ids:
                raise Warning('Company %s is not suitable in area %s.' % (self.company_id.name, self.area_id.name))
            vals.update({
                'company_ids': [Command.set(allowed_company_ids)],
                'area_id': self.area_id.id,
            })
        return vals