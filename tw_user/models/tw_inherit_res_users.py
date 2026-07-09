#!/usr/bin/python
#-*- coding: utf-8 -*-
# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
# 4: imports from odoo modules
from odoo.exceptions import AccessError

# 5: local imports

# 6: Import of unknown third party lib

class ResUsers(models.Model):
    _inherit = "res.users"

    # TODO: Aktifkan jika akses DB ke test teto sudah bisa, upgrade by db tw_user
    login_date = fields.Datetime(related='log_ids.create_date', string='Latest authentication', readonly=False, store=True)
    
    def get_formview_action(self, access_uid=None):
        """ Override this method to add access control for user form view """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_user.group_tw_res_users_form_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
