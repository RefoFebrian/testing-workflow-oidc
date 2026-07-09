# Copyright 2024 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    lat = fields.Float(
        string="Latitude",
        digits=(16, 8)
    )
    long = fields.Float(
        string="Longitude",
        digits=(16, 8)
    )
