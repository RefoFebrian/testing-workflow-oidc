# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompanyInherit(models.Model):
    _inherit = "res.company"

    is_allow_lead = fields.Boolean(
        string='Allow Auto Deal Lead',
        default=False,
        help='If checked, leads from this branch will be automatically dealt when created via API.'
    )
