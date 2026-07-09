# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime



class AccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"
    
    journal_purchase_return_id = fields.Many2one('account.journal', string='Journal Purchase Return')