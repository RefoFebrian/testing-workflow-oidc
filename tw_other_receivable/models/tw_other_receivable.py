from odoo import models, fields, api
from odoo.exceptions import UserError as Warning, ValidationError

class TwOtherReceivable(models.Model):
    _name = "tw.other.receivable"
    _order = "id desc"
    _inherit = "tw.account.payment"
    _description = "Other Receivable"
    
    # Add new fields
    type = fields.Selection(selection_add=[('other_receivable','Other Receivable')], ondelete={'other_receivable': 'set supplier_payment'})
    
    # 9: relation fields
    line_ids = fields.One2many('tw.other.receivable.line','payment_id','Line', context={'default_type':'cr'})
    line_cr_ids = fields.One2many('tw.other.receivable.line','payment_id','Credits',domain=[('type','=','cr')], context={'default_type':'cr'})
    line_dr_ids = fields.One2many('tw.other.receivable.line','payment_id','Debits',domain=[('type','=','dr')], context={'default_type':'dr'})
    line_wo_ids = fields.One2many('tw.other.receivable.line','payment_id','Writeoff',domain=[('type','=','wo')], context={'default_type':'wo'})    
    
    register_kwitansi_line_id = fields.Many2one('tw.register.kwitansi.line', string="No Kwitansi")
    duplicate_payment_ids = fields.Many2many('tw.other.receivable', compute='_compute_duplicate_payment_ids')
    source_payment_id = fields.Many2one(comodel_name='tw.other.receivable',related=False)
    invoice_ids = fields.Many2many('account.move', string="Invoices", relation='account_move_tw_other_receivable', column1='payment_id', column2='invoice_id',) # contains the invoice even if they don't have a journal entry and are not reconciled
    attachment_ids = fields.One2many('tw.attachment', 'res_id', string='Attachments',domain="[('res_model', '=', 'tw.other.receivable')]")
    
    # 11: compute/depends & on change methods
        
    # 13: action methods
    def action_post(self):
        if self.state != 'approved':
            raise UserError(f'Silakan refresh halaman Pembayaran ini, karena state sudah {self._get_state_value()}')
        
        self._update_amount_based_on_total_amount()
        return super().action_post()

    def action_print_kwitansi_other_receivable(self):
        self.ensure_one()

        return {
            'type':'ir.actions.act_window',
            'name': 'Pilih No Kwitansi',
            'res_model': 'tw.wizard.print.kwitansi',
            'view_mode':'form',
            'target':'new',
            'context':{'default_transaction_id': self.id, 'default_company_id': self.company_id.id, 'default_model_name':self._name, 'default_state':'open'},
        }

    def action_print_other_receivable(self):
        self.ensure_one()
        return self.env.ref('tw_other_receivable.action_report_other_receivable_print').report_action(self)
    
    # 14: private methods
    def _get_sequence_name(self):
        if self.type == 'other_receivable':
            seq_name = self.env['ir.sequence'].with_company(self.company_id).get_sequence_code('DN', self.company_id.code)
        else:
            seq_name = super()._get_sequence_name()
        return seq_name
    
    def _get_validate_type(self):
        type_list = super()._get_validate_type()
        type_list.append('other_receivable')
        return type_list

    def _update_amount_based_on_total_amount(self):
        if self.type =='other_receivable':
            self.amount = self.amount_total
        else:
            return super()._update_amount_based_on_total_amount()
    
    def _get_default_journal_id(self):
        if self.type == 'other_receivable':
            branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
            if not branch_setting_obj.account_setting_id:
                raise Warning(
                    "Account setting is not set for branch %s.\n"
                    "- Go to the Master Branch Setting.\n"
                    "- Set the 'Account Setting' to proceed.\n"
                    "This configuration is required to create accounting entries." 
                    % self.company_id.name
                )
            if not branch_setting_obj.account_setting_id.journal_other_receivable_id:
                raise Warning(
                        "Journal Other Receivable is not set for branch %s.\n"
                        "- Go to the Account Setting.\n"
                        "- Set the 'Journal Other Receivable'.\n"
                        "This configuration is required to create Other Receivable." 
                        % self.company_id.name
                    )
            return branch_setting_obj.account_setting_id.journal_other_receivable_id.id
        else:
            return super()._get_default_journal_id()
