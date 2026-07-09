# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date,timedelta,datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

class twLeadPayment(models.Model):
    _inherit = "tw.lead"
    _description = 'Lead Payment'

    # 7: defaults methods
    @api.model  
    def _get_default_date(self): 
        return date.today()
    
    def _get_due_date_options(self):
        return [(str(i), str(i)) for i in range(1, 32)]

    # 8: fields
    on_the_road = fields.Float(string='OTR (Rp)',digits=(12,0))
    discount = fields.Float(string='Diskon',default=0.00,digits=(12,0))
    down_payment = fields.Float(string='Uang Muka / DP (Rp)',digits=(12,0))
    payment_installment = fields.Float(string='Cicilan (Rp)',digits=(7,0))
    tenor = fields.Integer(string='Tenor')
    
    down_payment_date = fields.Date('Tgl Terima DP',default=_get_default_date)
    
    payment_type = fields.Selection([
        ('Cash', 'Cash'),
        ('Credit', 'Credit')], string='Jenis Pembelian')
    
    #TODO : Apakah ini due date atau tgl jatuh tempo? field tabrakan dengan field due_date dengan tipe date di tw_lead
    # due_date = fields.Selection(selection=_get_due_date_options,string='Tgl Jatuh Tempo')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods