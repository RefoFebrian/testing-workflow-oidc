# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command
from odoo.tools import SQL

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

class TWDealerSPKInherit(models.Model):
    _inherit = "tw.dealer.spk"

    # 7: defaults methods

    # 8: fields
    lead_count = fields.Integer(compute='_compute_lead_count')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _compute_lead_count(self):
        for spk in self:
            spk.lead_count = spk.env['tw.lead'].search_count([('name', '=', spk.lead_reference)])

    # 12: override methods

    # 13: action methods
    def action_view_lead(self):
        """ Opens the Lead associated with the SPK in a form view. """
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('LEAD'),
            'res_model': 'tw.lead',
            'view_mode': 'list,form',
            'target': 'current',
        }
        lead = self.env['tw.lead'].search([('name', '=', self.lead_reference)])
        if len(lead) > 1:
            action['view_mode'] = 'list,form'
            action['domain'] = [('id', 'in', lead.ids)]
        else:
            action['view_mode'] = 'form'
            action['res_id'] = lead.id
        
        return action

    # 14: private methods
    