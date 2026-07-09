# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwInheritBranchSetting(models.Model):
    _inherit = "tw.branch.setting"

    # 7: defaults methods

    # 8: fields
    minimal_dp_part_hotline = fields.Float('Minimal DP Part Hotline (%)', help="Minimal DP Part Hotline (dalam bentuk persentase)")

    @api.constrains('minimal_dp_part_hotline')
    def _check_minimal_dp_part_hotline(self):
        for record in self:
            if record.minimal_dp_part_hotline < 0 or record.minimal_dp_part_hotline > 100:
                raise ValidationError('Minimal DP Part Hotline harus antara 0 dan 100')
    

    