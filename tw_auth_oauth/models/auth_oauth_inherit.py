# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class AuthOAuthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    code = fields.Char(string='Provider Email Code', help='Provider Email Code for example: gmail,tunasgroup')