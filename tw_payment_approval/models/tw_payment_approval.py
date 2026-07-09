# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritAccountPaymentApproval(models.Model):
    _name = "tw.account.payment"
    _inherit = ["tw.account.payment","tw.approval.mixin"]

    # 8: fields
    state = fields.Selection(
        selection_add=[
            ('waiting_for_approval','Waiting For Approval'),
            ('approved','Approved'),
            ('in_process',)
        ], 
        ondelete={
            'waiting_for_approval': 'set default',
            'approved': 'set default',
        }
    )

    has_debit_lines = fields.Boolean(compute='_compute_has_debit_lines')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('line_dr_ids')
    def _compute_has_debit_lines(self):
        for record in self:
            record.has_debit_lines = bool(record.line_dr_ids)

    # 12: override methods
    
    # 13: action methods
    def action_post(self):
        super().action_post()
        self.filtered(lambda pay: pay.state in {False, 'draft', 'in_process', 'approved'}).state = 'in_process'

    def action_request_approval(self,value=False,code='other', **kwargs):
        if self.state != 'draft':
            raise Warning(f'Silakan refresh halaman Payment ini, karena State sudah {self._get_state_value()}')
                
        # Mengajukan permintaan approval
        # * Jika sudah ada module childs (seperti Purchase order Cancel, DSO Cancel dan lainnya) maka harus create pada menu di module tersebut
        self._validate_amount()
        code = self._get_approval_code()
        amount = self._get_approval_amount()
        return super().action_request_approval(amount, code)
    
    # 14: private methods
    def _get_approval_code(self):
        if self.payment_type == 'inbound':
            return 'receipt'
        elif self.payment_type == 'outbound':
            return 'payment'
        return 'other'

    def _get_unconfirmed_states(self):
        return ('draft', 'in_process','waiting_for_approval','approved')
    
    def _get_to_check_duplicate_states(self):
        return ('draft', 'in_process')

    def _get_approval_amount(self):
        self.ensure_one()
        total = 0.0
        jenis_trx = 'HC'
        for line in self.line_dr_ids :
            total += line.amount
            if line.move_line_id.move_id.name:
                split_trx = line.move_line_id.move_id.name.split('/')
                if split_trx[0] != 'HC':
                    jenis_trx = ''

        if self.payment_type == 'outbound' :
            if jenis_trx != 'HC':
                total = max(total, 2000001)

        elif self.payment_type == 'inbound' :
            total_cr = sum([line.amount for line in self.line_cr_ids])
            selisih = total_cr - total
            if selisih == 0:
                total = 1

        elif self.type == 'receive_payment':
            total = sum([line.amount for line in self.line_cr_ids])
        
        return total