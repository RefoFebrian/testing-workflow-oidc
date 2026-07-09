from datetime import datetime, date
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class StockDistribution(models.Model):
    _inherit = "tw.stock.distribution"
    
    mutation_request_id = fields.Many2one('tw.mutation.request', 'Mutation Request', ondelete='restrict', check_company=False)
    
    def action_reject_request(self):
        super().action_reject_request()
        if self.state == 'draft':
            self.mutation_request_id.suspend_security().write({'state': 'reject'})

    def action_confirm_qty(self):
        if self.state != 'approved':
            raise UserError(f'Silakan refresh halaman browser Anda. State sudah {self._get_state_value()}')
        super().action_confirm_qty()
        total_approved_qty = sum(line.approved_qty for line in self.stock_distribution_ids)
        if total_approved_qty > 0:
            self.mutation_request_id.suspend_security().write({'state': 'open'})

    def action_done(self):
        """Override action_done to also mark linked Mutation Request as done."""
        super().action_done()
        
        if self.mutation_request_id and self.mutation_request_id.state not in ('done', 'cancel'):
            self.mutation_request_id.action_done()