# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools import SQL

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class TWDealerSaleOrderInherit(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    lead_id = fields.Many2one('tw.lead', "Lead", help="Lead associated with this Sale Order.")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_view_lead(self):
        self.ensure_one()
        if not self.lead_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('No Lead Reference is linked to this sale order.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': _('LEAD'),
            'res_model': 'tw.lead',
            'res_id': self.lead_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'form_view_ref': 'tw_lead.tw_lead_crm_lead_form_view',
            }
        }

    # 14: private methods
