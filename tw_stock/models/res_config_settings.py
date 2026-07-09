# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    incoming_valuation_on_last_route = fields.Boolean("Valuation on last route",related='company_id.incoming_valuation_on_last_route',readonly=False)
    