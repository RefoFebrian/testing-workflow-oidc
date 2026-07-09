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

class TWBoomMasterEscalation(models.Model):
    _name = "tw.boom.master.escalation"
    _description = "TW Boom Master Escalation"


    # 7: defaults methods
    
    # 8: fields
    unit = fields.Selection([
        ('day', 'Hari (H)'),
        ('week', 'Minggu (W)'),
        ('month', 'Bulan (M)'),
    ], string='Unit', default='day')
    
    interval = fields.Integer(string='Interval', default=0)

    escalation_hour = fields.Selection(selection=[
        ('08','08'),
        ('09','09'),
        ('10','10'),
        ('11','11'),
        ('12','12'),
        ('13','13'),
        ('14','14'),
        ('15','15'),
        ('16','16')], string='Eskalasi Jam',  help='')

    escalation_minute = fields.Selection(selection=[
        ('00','00'),
        ('15','15'),
        ('20','20'),
        ('25','25'),
        ('30','30'),
        ('35','35'),
        ('40','40'),
        ('45','45'),
        ('50','50'),
        ('55','55')], string='Eskalasi Menit',  help='')

    is_send_message_scheduled = fields.Boolean(string='Send Message Scheduled?', default=False)

    # 9: relation fields
    job_id = fields.Many2one('hr.job', 'Job')
    category_id = fields.Many2one('tw.boom.category', 'Category')

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    