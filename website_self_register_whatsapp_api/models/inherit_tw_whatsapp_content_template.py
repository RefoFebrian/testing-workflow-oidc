# -*- coding: utf-8 -*-

from odoo import models, fields

class InheritWhatsappContentTemplate(models.Model):
    _inherit = "tw.whatsapp.content.template"

    # Parent doesn't have 'type' selection field, so we define it here as a new field
    type = fields.Selection([('self_register', 'Self Register')], string='Type')