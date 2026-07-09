# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib


class TwAccountSetting(models.Model):
    _name = "tw.account.setting"
    _description = 'Master Data Account Setting'

    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string="Description")
    rounding_amount = fields.Float(string='Nilai Pembulatan',digits='Product Price')
    

    # 9: relation fields
    account_rounding_id = fields.Many2one('account.account', string='Account Pembulatan')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super(TwAccountSetting, self).create(vals_list)
        return create

    def write(self,vals):
        return super(TwAccountSetting, self).write(vals)
    
    def unlink(self):
        raise UserError(_('Warning! \nCannot delete records!'))

    def get_account_setting(self, field_name, default=None, raise_if_none=False):
        """
        Global method to get account setting value by field name
        
        :param str field_name: Name of the field to get value from
        :param any default: Default value if no record or field not found
        :param bool raise_if_none: If True, raises an error when value is None
        :return: Field value or default
        :raises: UserError if raise_if_none is True and value is None
        """
        if not field_name:
            if raise_if_none:
                raise UserError(_("Field name is required"))
            return default
            
        self.ensure_one()
            
        if not hasattr(self, field_name):
            if raise_if_none:
                raise UserError(_("Field '%s' not found in account settings") % field_name)
            return default
            
        value = self[field_name]
        if not value and raise_if_none:
            field_string = self._fields[field_name].string if field_name in self._fields else field_name
            raise UserError(_("Value for field '%s' is not set in account settings") % field_string)
            
        return value if value else default

    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_account_setting.group_tw_account_setting_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res

    # 13: action methods

    # 14: private methods


