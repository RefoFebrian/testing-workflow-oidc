# -*- coding: utf-8 -*-

# 3: imports of odoo
from odoo import models, fields


class TwBranchSettingDGIInbound(models.Model):
    """Extend tw.branch.setting with DGI Inbound configuration."""
    _inherit = "tw.branch.setting"

    # 8: fields
    dgi_auto_confirm_po = fields.Boolean(
        string='DGI Auto Confirm PO',
        default=False,
        help="Jika aktif, Purchase Order yang dibuat dari DGI (UINB) akan otomatis di-Confirm, "
             "membuat Picking Transfer (Incoming) dan Draft Vendor Bill (Invoice).",
    )
