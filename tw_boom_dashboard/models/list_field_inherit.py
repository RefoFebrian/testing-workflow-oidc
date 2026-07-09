# -*- coding: utf-8 -*-
from odoo import fields, models


class ListFieldsInherit(models.Model):
    _inherit = "list.fields"

    measure_color = fields.Char(
        string="Color",
        default="#000000",
        help="Color for the measured field column"
    )
    label = fields.Char(
        string="Label",
        help="Custom label for the measured field column. If not set, the field name will be used."
    )
