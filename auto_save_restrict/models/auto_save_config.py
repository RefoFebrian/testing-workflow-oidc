from odoo import models, fields

class AutoSaveRule(models.Model):
    _inherit = "res.users"

    is_auto_save = fields.Boolean(
        string="Auto Save",
        default=True,
        help="If checked, auto-save will be enabled"
    )

