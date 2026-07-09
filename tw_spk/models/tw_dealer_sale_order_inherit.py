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
    spk_id = fields.Many2one("tw.dealer.spk", "SPK", help="SPK associated with this Sale Order.")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_done(self):
        self.spk_id.write({
            'state': 'done',
        })
        super().action_done()

    def action_view_spk(self):
        self.ensure_one()
        if not self.spk_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('No SPK Reference is linked to this sale order.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': _('SPK'),
            'res_model': 'tw.dealer.spk',
            'res_id': self.spk_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'form_view_ref': 'tw_dealer_spk.tw_dealer_spk_form_view',
            }
        }

    # 14: private methods
