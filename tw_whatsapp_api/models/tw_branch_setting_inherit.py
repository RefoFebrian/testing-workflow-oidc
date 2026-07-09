# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

class TwBranchSettingInherit(models.Model):
    _inherit = "tw.branch.setting"

    official_wa_config_id = fields.Many2one('tw.api.configuration', string='Official WA Config')
    unofficial_wa_config_id = fields.Many2one('tw.api.configuration', string='Unofficial WA Config')