from odoo import models, fields, api

class BranchInheritArea(models.Model):
    _inherit = "res.company"

    @api.model_create_multi
    def create(self, vals_list):
        creates = super(BranchInheritArea, self).create(vals_list)
        for create in creates:
            if create.parent_id:
                create._create_or_link_area()
        return creates

    def _create_or_link_area(self):
        existing_area = self.env['res.area'].sudo().search([('code', '=', self.code)], limit=1)
        
        if existing_area:
            existing_area.sudo().write({'company_ids': [(4, self.id)]})
        else:
            self.env['res.area'].sudo().create({'name': self.name, 'description': self.name, 'code': self.code, 'company_ids': [(4, self.id)]})
