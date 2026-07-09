# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
import requests
import json

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
import logging
_logger = logging.getLogger(__name__)

# 5: local imports

# 6: Import of unknown third party lib

class TWStockPickingB2BApi(models.Model):
    _inherit = "stock.picking"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def _process_validate_picking(self):
        res = super(TWStockPickingB2BApi, self)._process_validate_picking()
        b2b_api_ev_obj = self.env['tw.b2b.api.ev'].search([
            ('ship_list_number', '=', self.mft_reference),
            ('state', 'in', ['waiting', 'assigned'])
        ], limit=1)
        if b2b_api_ev_obj:
            for line in b2b_api_ev_obj.line_ids:
                move_line_obj = self.env['stock.move.line'].search([
                    ('picking_id', '=', self.id),
                    ('lot_id.name', '=', line.serial_number)
                ], limit=1)
                if move_line_obj:
                    line.suspend_security().write({'state': 'done'})
            
            if b2b_api_ev_obj.state == 'waiting' or not b2b_api_ev_obj.picking_id:
                b2b_api_ev_obj.suspend_security().write({
                    'picking_id': self.id,
                    'state': 'assigned'
                })

            if all(line.state == 'done' for line in b2b_api_ev_obj.line_ids):
                b2b_api_ev_obj.suspend_security().write({'state': 'done'})

        return res

    # 13: action methods

    # 14: private methods