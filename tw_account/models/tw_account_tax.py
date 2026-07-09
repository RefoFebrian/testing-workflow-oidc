# -*- coding: utf-8 -*-

# 1: imports of python lib
from contextlib import contextmanager
from datetime import datetime
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# 4:  imports from odoo modules


# 5: local imports

# 6: Import of unknown third party lib

class InheritAccountTax(models.Model):
    _inherit = "account.tax"
    _order = "id desc"
    
    # 12: override methods
    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_account.group_tw_account_tax_form_read'):
            raise UserError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
    
    @api.model
    def _prepare_tax_lines(self, base_lines, company, tax_lines=None):
        res = super()._prepare_tax_lines(base_lines, company, tax_lines)
        for tax_line in res.get('tax_lines_to_add', []):
            tax_line['company_id'] = company.id
        return res