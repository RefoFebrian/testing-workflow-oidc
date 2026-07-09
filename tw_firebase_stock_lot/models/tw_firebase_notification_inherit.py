#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import timedelta, datetime, date
import calendar
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
from pyfcm import FCMNotification
from lxml.html import fromstring, tostring
from lxml.html import builder as E

class InheritStockLotFirebaseNotification(models.Model):
    _inherit = "tw.firebase.notification"
    

    lot_id = fields.Many2one(comodel_name="stock.lot",  string="Engine",  readonly=True, help="")