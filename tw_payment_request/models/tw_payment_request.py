from odoo import models, fields, api
from odoo.exceptions import UserError as Warning, ValidationError

class AccountPaymentInherit(models.Model):
    _name = "tw.payment.request"
    _inherit = "tw.account.payment"
    _description = "Payment Request"
    
    # Add new fields
    type = fields.Selection(selection_add=[('payment_request','Payment Request')], ondelete={'payment_request': 'set supplier_payment'})
    transaction_type = fields.Selection([
        ('non_recurring', 'Non-Recurring'),
        ('recurring', 'Recurring'),
    ], string='Transaction Type', default='non_recurring', required=True)
    is_paid = fields.Boolean(string='Is Paid', compute='_compute_is_paid', default=False,store=True)

    # 9: relation fields
    line_ids = fields.One2many('tw.payment.request.line','payment_id','Line', context={'default_type':'cr'})
    line_cr_ids = fields.One2many('tw.payment.request.line','payment_id','Credits',domain=[('type','=','cr')], context={'default_type':'cr'})
    line_dr_ids = fields.One2many('tw.payment.request.line','payment_id','Debits',domain=[('type','=','dr')], context={'default_type':'dr'})
    line_wo_ids = fields.One2many('tw.payment.request.line','payment_id','Writeoff',domain=[('type','=','wo')], context={'default_type':'wo'})    
    
    duplicate_payment_ids = fields.Many2many('tw.payment.request', compute='_compute_duplicate_payment_ids')
    source_payment_id = fields.Many2one(comodel_name='tw.payment.request',related=False)
    invoice_ids = fields.Many2many('account.move', string="Invoices", relation='account_move_tw_payment_request', column1='payment_id', column2='invoice_id',) # contains the invoice even if they don't have a journal entry and are not reconciled
    attachment_ids = fields.One2many('tw.attachment', 'res_id', string='Attachments',domain="[('res_model', '=', 'tw.payment.request')]")
    account_payment_ids = fields.Many2many('tw.account.payment', relation='tw_payment_request_account_payment_rel', string='Account Payment', ondelete='cascade', copy=False)
    
    payment_request_type_id = fields.Many2one('tw.payment.request.type', string='Payment Request Type')
    payable_move_line_ids = fields.Many2many('account.move.line', compute='_compute_payable_move_line_ids', string='Payable Move Line', store=True)
    
    # 11: compute/depends & on change methods
    @api.depends('move_id.line_ids')
    def _compute_payable_move_line_ids(self):
        for rec in self:
            rec.payable_move_line_ids = rec.move_id.line_ids.filtered(lambda x: x.account_id.account_type == 'liability_payable')
    
    @api.depends('payable_move_line_ids.full_reconcile_id')
    def _compute_is_paid(self):
        for rec in self:
            lines = rec.payable_move_line_ids
            rec.is_paid = bool(lines) and all(line.full_reconcile_id for line in lines)
    
    @api.onchange('transaction_type')
    def onchange_transaction_type(self):
        self.line_dr_ids = False
        self.payment_request_type_id = False
    
    @api.onchange('payment_request_type_id')
    def onchange_payment_request_type_id(self):
        self.line_dr_ids = False
        
    # 13: action methods
    def action_post(self):
        self.with_company(self.company_id)._update_amount_based_on_total_amount()
        payment_obj = self.with_company(self.company_id)
        return super(AccountPaymentInherit, payment_obj).action_post()
    
    def action_validate(self):
        self.with_company(self.company_id)._update_amount_based_on_total_amount()
        payment_obj = self.with_company(self.company_id)
        return super(AccountPaymentInherit, payment_obj).action_validate()

    def action_view_payment(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("tw_payment.tw_supplier_payment_action")
        context = eval(action.get('context')) if action.get('context') else {}
        context.update({
            'create':False,
        })
        action['context'] = context

        payments = self.account_payment_ids
        if len(payments) == 1:
            form_view = self.env.ref('tw_payment.tw_account_payment_form_view')
            action.update({
                'views': [(form_view.id, 'form')],
                'res_id': payments.id,
                'domain': [],
            })
        else:
            action['domain'] = [('id', 'in', payments.ids)]
        return action
    
    def action_print_payment_request(self):
        self.ensure_one()
        return self.env.ref('tw_payment_request.action_report_tw_payment_request').report_action(self.id)
        
    # 14: private methods
    def _get_sequence_name(self):
        if self.type == 'payment_request':
            seq_name = self.env['ir.sequence'].with_company(self.company_id).get_sequence_code('NC', self.company_id.code)
        else:
            seq_name = super()._get_sequence_name()
        return seq_name
    
    def _get_validate_type(self):
        type_list = super()._get_validate_type()
        type_list.append('payment_request')
        return type_list
    
    def _update_amount_based_on_total_amount(self):
        if self.type =='payment_request':
            self.amount = self.amount_total
        else:
            return super()._update_amount_based_on_total_amount()

    def _get_default_journal_id(self):
        if self.type == 'payment_request':
            branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
            if not branch_setting_obj.account_setting_id:
                raise Warning(
                    "Account setting is not set for branch %s.\n"
                    "- Go to the Master Branch Setting.\n"
                    "- Set the 'Account Setting' to proceed.\n"
                    "This configuration is required to create accounting entries." 
                    % self.company_id.name
                )
            if not branch_setting_obj.account_setting_id.journal_payment_request_id:
                raise Warning(
                        "Journal Payment Request is not set for branch %s.\n"
                        "- Go to the Account Setting.\n"
                        "- Set the 'Journal Payment Request'.\n"
                        "This configuration is required to create Accrue Payment Request." 
                        % self.company_id.name
                    )
            return branch_setting_obj.account_setting_id.journal_payment_request_id.id
        else:
            return super()._get_default_journal_id()
            
        