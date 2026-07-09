from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    attachment_required = fields.Boolean(string='Attachment Required', config_parameter='tw_advance_payment.attachment_required', help="Default attachment required")

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('tw_advance_payment.attachment_required', self.attachment_required)

    @api.model
    def get_values(self):
        res = super().get_values()
        attachment_required = self.env['ir.config_parameter'].sudo().get_param('tw_advance_payment.attachment_required')
        res.update(attachment_required=attachment_required)
        return res
