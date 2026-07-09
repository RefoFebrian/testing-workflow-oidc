# -*- coding: utf-8 -*-

from odoo import fields, models

class TwWorkOrderLinePackage(models.Model):
    _inherit = "tw.work.order.line"

    service_package_id = fields.Many2one('tw.service.package', string='Package')
