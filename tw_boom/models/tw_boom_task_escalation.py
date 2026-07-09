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

class TWBoomTaskEscalation(models.Model):
    _name = "tw.boom.task.escalation"
    _description = "TW Boom Task Eskalasi"
    _order = "id desc"
    
    # 7: defaults methods
    

    # 8: fields
    note = fields.Char(string="Keterangan")

    unit = fields.Selection([
        ('day', 'Hari (H)'),
        ('week', 'Minggu (W)'),
        ('month', 'Bulan (M)'),
    ], string='Unit', default='day')
    
    interval = fields.Integer(string='Interval')

    state = fields.Selection(selection=[
        ('open', 'Open'),
        ('done', 'Done')], default='open',  string='Status',  help='')
    

    # 9: relation fields
    task_id = fields.Many2one('tw.boom.task', 'Task')
    pic_id =  fields.Many2one('hr.employee', 'PIC Eskalasi')
    job_id = fields.Many2one('hr.job', 'PIC Job Eskalasi')

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods