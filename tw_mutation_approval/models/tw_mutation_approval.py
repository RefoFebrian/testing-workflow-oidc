from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError


class ApprovalMutationOrder(models.Model):
    _name = "tw.mutation.order"
    _inherit = ["tw.mutation.order", "tw.approval.mixin"]
    # description : Approval Mutation Order

    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('confirm',),
        ('done',),
        ('cancelled',),
    ], string="Status")

    is_approval_required = fields.Boolean(
        string="Is Approval Required",
        compute="_compute_is_approval_required",
        store=True,
    )

    @api.depends('company_id.branch_type_id.value')
    def _compute_is_approval_required(self):
        for record in self:
            record.is_approval_required = bool(
                record.company_id and record.company_id.branch_type_id.value == 'MD'
            )

    def action_confirm(self):
        if self.state not in ('draft', 'approved'):
            raise Warning(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')

        return super().action_confirm()

    def validate_order(self):
        if not self.mutation_order_ids:
            raise UserError("Perhatian!\nTab Mutation Line tidak boleh kosong!")
        self.renew_available()
        self.mutation_order_ids._validate_order()
        return super().validate_order()
    
        