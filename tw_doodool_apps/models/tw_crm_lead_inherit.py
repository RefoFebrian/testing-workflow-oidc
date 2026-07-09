# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CRMLead(models.Model):
    _inherit = "tw.lead"

    version_code = fields.Char()
    version_name = fields.Char()
