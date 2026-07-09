# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date 

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwBranchSetting(models.Model):
    _inherit = "tw.branch.setting"

    is_po_need_approval = fields.Boolean(string="PO Need Approval",default = True)