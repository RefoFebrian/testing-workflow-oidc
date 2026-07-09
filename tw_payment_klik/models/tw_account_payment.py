from datetime import datetime
from odoo import models, fields, api

class TwAccountPayment(models.Model):
    _inherit = "tw.account.payment"
    
    is_payment_klik = fields.Boolean('Payment Klik ?')
    payment_klik_uid = fields.Many2one('res.users','Payment Klik by')
    payment_klik_date = fields.Datetime('Payment Klik on')

    def write(self, vals):
        if vals.get('state','') == 'draft' and self.state != 'draft':
            # Reset Payment Klik (formerly reset_payment_klik, if user doing cancel approval or reset transaction to draft)
            vals.update({
                'is_payment_klik': False,
                'payment_klik_uid': False,
                'payment_klik_date': False
            })
        
        return super().write(vals)

    def action_klik_payment(self):
        self.write({
            'is_payment_klik': True,
            'payment_klik_uid': self._uid,
            'payment_klik_date': datetime.now(),
        })
