# -*- coding: utf-8 -*-

from odoo import api, fields, models, modules, _


class IrModel(models.Model):
    _inherit = "ir.model"

    rest_api = fields.Boolean('REST API', default=True, help="Enable REST API for this object/model")
