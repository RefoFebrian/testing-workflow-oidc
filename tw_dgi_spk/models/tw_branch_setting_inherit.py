# -*- coding: utf-8 -*-

from odoo import fields, models


class TwBranchSettingInherit(models.Model):
    _inherit = "tw.branch.setting"

    is_dgi_dso_required = fields.Boolean(
        string="CDB Data Mandatory (DGI DSO)?",
        help=(
            "If enabled, DSO from DGI cannot be confirmed until the internal "
            "mandatory customer data is completed."
        ),
    )
