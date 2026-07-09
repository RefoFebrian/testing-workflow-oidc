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

class TWStockLotB2BApi(models.Model):
    _inherit = "stock.lot"
    
    # 7: defaults methods

    # 8: fields
    voucher_acc = fields.Char(string='Voucher ACC')
    jenis_acc = fields.Char(string='Jenis Acc')
    box_number = fields.Char(string='Box Number')
    packing_number = fields.Char(string='Packing Number')
    carton_number = fields.Char(string='Carton Number')
    category_acc = fields.Selection([
        ('EVBT','Battery'),
        ('EVCH','Charger'),
    ], string='Category ACC')
    note_api_ev = fields.Text('Note API EV')
    actual_ev_md_receive_date = fields.Datetime(string='Actual Accessories EV MD Receive Date', help='MD Admission Accessories EV Receive Date')

    # 9: relation fields
    #? TO DO: Apakah masih menggunakan reference lot untuk EV
    # lot_reference_ids = fields.One2many('tw.reference.lot', 'lot_id', string='Lot Reference')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_reset_status_ev(self):
        self.suspend_security().write({
            'note_api_ev': False,
            'actual_ev_md_receive_date': False
        })

    # 14: private methods