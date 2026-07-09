from odoo import models, fields, api

class ResUserArea(models.Model):
    _inherit = "res.users"

    # TODO: butuh dibuat di res_users, lalu jika ya buat module sendiri untuk tw_area_user? TBD
    area_id = fields.Many2one('res.area', string='Area')

    @api.onchange('area_id')
    def _onchange_area_id(self):
        if self.area_id:
            self.company_ids = self.area_id.company_ids.ids
        else:
            self.company_ids = False