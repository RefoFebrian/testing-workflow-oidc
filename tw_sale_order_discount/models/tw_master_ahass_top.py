from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class MasterAhassTop(models.Model):
    _name = "tw.master.ahass.top"
    _description = "Master AHASS TOP"

    name = fields.Char('Name', compute='_compute_name')
    partner_id = fields.Many2one('res.partner',string='Dealer', domain=[('category_id.name','in',['Dealer'])])
    master_ahass_top_ids = fields.One2many('tw.master.ahass.top.line', 'master_ahass_top_id', string='Master AHASS TOP Line')

    def _compute_name(self):
        for record in self:
            code = record.partner_id.code or record.partner_id.identification_number
            name = f"[{code}] {record.partner_id.name} "
            record.name = name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('partner_id'):
                partner_obj = self.env['res.partner'].suspend_security().browse(vals['partner_id'])

                code = partner_obj.code or partner_obj.identification_number
                vals['name'] = f"[{code}] {partner_obj.name} "
        return super(MasterAhassTop, self).create(vals)
