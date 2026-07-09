from odoo import models, fields, api
from odoo.exceptions import UserError as Warning, ValidationError

class AccountPaymentInherit(models.Model):
    _inherit = "tw.payment.request"
    
    # 9: relation fields
    
    # 11: compute/depends & on change methods
        
    # 13: action methods
    def action_upload_line(self):
        if self.state != 'draft':
            raise Warning("Payment must be in draft state to upload line")
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.payment.request.upload',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_payment_id': self.id},
            'views': [(False, 'form')],
        }
    
    # 14: private methods
    