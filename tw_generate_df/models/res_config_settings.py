from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    permata_account_beneficiary_account = fields.Char(string="Permata Account Beneficiary Account",config_parameter='tw_generate_df.permata_account_beneficiary_account')
    permata_account_partner_id = fields.Char(string="Permata Account Partner Id",config_parameter='tw_generate_df.permata_account_partner_id')
    account_bri = fields.Char(string="BRI Account",config_parameter='tw_generate_df.account_bri')

    def set_values(self):
        super().set_values()
        if self.permata_account_beneficiary_account:    
            self.env['ir.config_parameter'].sudo().set_param(
                'tw_generate_df.permata_account_beneficiary_account', self.permata_account_beneficiary_account)
            self.env['ir.config_parameter'].sudo().set_param(
                'tw_generate_df.permata_account_partner_id', self.permata_account_partner_id)
        else:
            self.env['ir.config_parameter'].sudo().set_param(
                'tw_generate_df.permata_account_beneficiary_account', '')
            self.env['ir.config_parameter'].sudo().set_param(
                'tw_generate_df.permata_account_partner_id', '')

        if self.account_bri:
            self.env['ir.config_parameter'].sudo().set_param(
                'tw_generate_df.account_bri', self.account_bri)
        else:
            self.env['ir.config_parameter'].sudo().set_param(
                'tw_generate_df.account_bri', '')

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            permata_account_beneficiary_account=self.env['ir.config_parameter'].sudo().get_param(
                'tw_generate_df.permata_account_beneficiary_account',default=''),
            permata_account_partner_id=self.env['ir.config_parameter'].sudo().get_param(
                'tw_generate_df.permata_account_partner_id',default=''),
            account_bri=self.env['ir.config_parameter'].sudo().get_param(
                'tw_generate_df.account_bri',default=''))
        return res