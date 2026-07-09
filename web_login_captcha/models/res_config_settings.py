# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    recaptcha_version = fields.Selection([
        ('off', 'Off'),
        ('v3_invisible', 'ReCAPTCHA v3 (Invisible)'),
        ('v2_checkbox', 'ReCAPTCHA v2 (Checkbox)'),
    ], string="ReCAPTCHA Version", default='off', config_parameter='web_login_captcha.recaptcha_version')
