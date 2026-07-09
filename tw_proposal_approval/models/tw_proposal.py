from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class TwProposal(models.Model):
    _name = "tw.proposal"
    _inherit = ["tw.proposal", "tw.approval.mixin"]
    
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('done',),
        ('reject','Rejected'),
    ])

    def get_approve_additional_vals(self):
        # TODO: ini cek berdasarkan wajib approve oleh Job Khusus
        # self._check_budget_approval()
        return super().get_approve_additional_vals()
    
    def generate_matrix_approval(self,value=0,code='other'):
        if self.category == 'recurring':
            code='recurring'
        else:
            code='non_recurring'
        return super().generate_matrix_approval(value=value,code=code)

    def _check_budget_approval(self):
        check_model_id = self.env['ir.model'].suspend_security().search([('model', '=', self._name)]).id
        get_proposal_limit_query = """
            SELECT COALESCE(MAX(al.limit),0)
            FROM tw_proposal prop
            JOIN tw_approval_line al ON al.transaction_id = prop.id AND al.model_id = %d
            WHERE prop.id = %d
            AND al.state = 'approve'
        """ % (check_model_id, self.id)
        self._cr.execute(get_proposal_limit_query)
        limit_ress = self._cr.fetchone()
        if limit_ress[0] <= 0: # belum approve by budget
            # limit 1 khusus staf budget-checking
            get_budget_group_query = """
                SELECT 
                    CONCAT(md.module, '.', md.name) AS group_name
                FROM res_groups md
                JOIN tw_approval_line al ON md.id = al.group_id AND al.model_id = %d AND al.transaction_id = %d
                WHERE al.limit = 1
            """ % (check_model_id, self.id)
            self._cr.execute(get_budget_group_query)
            group_ress = self._cr.fetchone()
            if not group_ress:
                raise Warning('Matrix approval by staf budget tidak ditemukan. Cek kembali matrix approval Proposal!')
            if not self.env.user.has_group(str(group_ress[0])):
                raise Warning('Proposal belum di-approve oleh staf budget!')
        return True



    
   