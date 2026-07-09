from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    report_date_range_limit = fields.Integer(string='Limit Penarikan Report', config_parameter='tw_base.report_date_range_limit', help="Default limit penarikan report dalam hitungan hari")

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('tw_base.report_date_range_limit', self.report_date_range_limit)

    @api.model
    def get_values(self):
        res = super().get_values()
        limit = int(self.env['ir.config_parameter'].sudo().get_param('tw_base.report_date_range_limit'))
        res.update(report_date_range_limit=limit)
        return res
