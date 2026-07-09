# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwB2BErrorLog(models.Model):
    _name = "tw.b2b.error.log"
    _description = "TW B2B Error Log"
    _order = "id desc"

    # 7: defaults methods

    # 8: fields
    name = fields.Text(string="Error", help="Error description")
    datetime = fields.Datetime(string="Date", default=fields.Datetime.now())
    state = fields.Selection([
        ('open','Open'),
        ('done','Done')
    ], default='open')
    
    # 9: relation fields
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods