# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TWBoomMasterQuotes(models.Model):
    _name = "tw.boom.master.quotes"
    _description = "TW Boom Master Quotes"
    _order = "id desc"

    name = fields.Char('Name')
    author = fields.Char('Author')

    time_periode = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Time Periode')

    category = fields.Selection([
        ('random', 'Random'),
        ('specific_date', 'Specific Date'),
        ('specific_day', 'Specific Day'),
    ], string='Category')

    day_name = fields.Selection([
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday')
    ], string='Day')

    is_active = fields.Boolean('Active?', default=True) 

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
