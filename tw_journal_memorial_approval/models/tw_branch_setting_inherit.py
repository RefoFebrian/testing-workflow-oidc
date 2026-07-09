# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwBranchSetting(models.Model):
    _inherit = "tw.branch.setting"

    is_need_approval_jm_cancel = fields.Boolean(string="Need Approval JM Cancel", default=True)
