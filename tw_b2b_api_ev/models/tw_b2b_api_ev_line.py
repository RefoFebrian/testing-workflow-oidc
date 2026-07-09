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

class TWB2BApiEvLine(models.Model):
    _name = "tw.b2b.api.ev.line"
    _description = "TW B2B API EV Line"
    _rec_name = 'part_code'
    
    # 7: defaults methods
    def _get_default_date(self):
        return date.today().strftime("%Y-%m-%d")
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    part_code = fields.Char(string='Kode Part')
    part_desc = fields.Char(string='Deskripsi Part')
    serial_number = fields.Char(string='Nomor Serial')
    box_number = fields.Char(string='Nomor Box')
    carton_number = fields.Char(string='Nomor Carton')
    type_acc = fields.Selection([
        ('EVBT', 'EVBT (Battery)'),
        ('EVCH', 'EVCH (Charger)')
    ], string='Type Acc')
    state = fields.Selection([
        ('assigned','Ready to transfer'),
        ('done','Done'),
    ], string='State', default='assigned')

    # 9: relation fields
    b2b_api_ev_id = fields.Many2one('tw.b2b.api.ev', string='B2B API EV')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_open_lot(self):
        self.ensure_one()
        lot_obj = self.env['stock.lot'].suspend_security().search([('name', '=', self.serial_number)])
        if not lot_obj:
            raise Warning('serial number has not been generated.')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'form',
            'view_id': self.env.ref('tw_stock.tw_stock_lot_form_view').id,
            'res_id': lot_obj.id
        }

    # 14: private methods