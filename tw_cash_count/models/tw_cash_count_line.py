# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwCashCountLine(models.Model):
    _name = "tw.cash.count.line"
    _description = "Cash Count Line"

    # 7: defaults methods
    
    # 8: fields
    name = fields.Char('Name')
    journal = fields.Char('Journal',index=True)
    status = fields.Char('Status')
    date = fields.Date('Date')
    description = fields.Char('Description')
    amount = fields.Float('Amount Sistem')
    physical_amount = fields.Float('Amount Fisik')
    selisih = fields.Float('Amount Selisih',compute='_compute_selisih')
    note = fields.Char('Keterangan')
    type = fields.Selection([
        ('cash','Cash'),
        ('petty_cash','Petty Cash'),
        ('reimburse_petty_cash','Reimburse Petty Cash')],index=True)
    

    # 9: relation fields
    cash_count_id = fields.Many2one('tw.cash.count','Cash Count',ondelete='cascade')
    journal_id = fields.Many2one('account.journal','Journal ID')
    validation_id = fields.Many2one('tw.cash.count.validation','Validasi',domain="[('type','=',type)]")

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods
    @api.depends('amount','physical_amount')
    def _compute_selisih(self):
        for me in self:
            me.selisih = 0
            if me.amount and me.physical_amount:
                me.selisih = me.amount - me.physical_amount

    @api.onchange('validation_id')
    def onchange_validasi(self):
        self.note = False
        if self.validation_id:
            self.note = self.validation_id.note


    # 12: Override Methods

    # 13: Action Methods

    # 14: Private Methods

        
