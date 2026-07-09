# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAdvancePayment(models.Model):
    _name = "tw.advance.payment"
    _order = "id desc"
    _inherit = ["tw.account.payment", "tw.attachment.mixin"]
    _description = "Advance Payment"

    def _get_default_date(self): 
        return datetime.now().date()

    # Add new fields
    state = fields.Selection(
        selection_add=[
            ('confirm', 'Confirmed'),
            ('done', 'Done')
        ], 
        ondelete={
            'confirm': 'set default',
            'done': 'set default',
        }
    )
    type = fields.Selection(selection_add=[('advance_payment','Advance Payment')], ondelete={'advance_payment': 'set supplier_payment'}) 
    email = fields.Char(string='Email')
    date = fields.Date(string='Date')
    description = fields.Text(string='Description')
    user_balance = fields.Float(string='Balance',compute='_compute_user_balance')
    account_number = fields.Char('No Rekening Tujuan')

    # 8.1 Audit Trail fields
    done_uid = fields.Many2one('res.users','Done by')
    done_date = fields.Datetime('Done on')

    # 9: relation fields
    employee_id = fields.Many2one('hr.employee',string='Employee',domain="[('company_id', '=', company_id)]",default=lambda self: self.env.user.employee_id)
    account_avp_id = fields.Many2one(
        comodel_name='account.account', 
        string='Account Advance Payment', 
        compute='_compute_account_avp_id', 
        store=True, 
        readonly=False
    )
    payment_ids = fields.Many2many('tw.account.payment', relation='tw_advance_payment_account_payment_rel', string='Payment')
    
    line_ids = fields.One2many('tw.advance.payment.line','payment_id','Line', context={'default_type':'cr'})
    line_cr_ids = fields.One2many('tw.advance.payment.line','payment_id','Credits',domain=[('type','=','cr')], context={'default_type':'cr'})
    line_dr_ids = fields.One2many('tw.advance.payment.line','payment_id','Debits',domain=[('type','=','dr')], context={'default_type':'dr'})
    line_wo_ids = fields.One2many('tw.advance.payment.line','payment_id','Writeoff',domain=[('type','=','wo')], context={'default_type':'wo'})    
    duplicate_payment_ids = fields.Many2many('tw.advance.payment', compute='_compute_duplicate_payment_ids')
    source_payment_id = fields.Many2one(comodel_name='tw.advance.payment',related=False)
    invoice_ids = fields.Many2many('account.move', string="Invoices", relation='account_move_tw_advance_payment', column1='payment_id', column2='invoice_id',) # contains the invoice even if they don't have a journal entry and are not reconciled

    @api.depends('journal_id')
    def _compute_account_avp_id(self):
        for record in self:
            record.account_avp_id = record.journal_id.default_debit_account_id

    # 11: compute/depends & on change methods
    def _compute_user_balance(self):
        for record in self:
            record.user_balance = 0
            if record.employee_id:
                user_balance = self.search([('employee_id', '=', record.employee_id.id),('state', '=', 'confirm')], order='id desc')
                if user_balance:
                    record.user_balance = sum(user_balance.mapped('amount'))
                else:
                    record.user_balance = 0

    @api.onchange('amount','description')
    def onchange_amount_description(self):
        if self.type == 'advance_payment':
            self._create_line_avp()
    
    @api.onchange('due_date')
    def _onchange_due_date(self):
        if self.type == 'advance_payment':
            now = date.today()
            if self.due_date and self.due_date < now:
                self.due_date = False
                raise Warning('Tanggal Due Date tidak boleh kurang dari hari ini')
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        Set partner_bank_id directly from employee's bank_account_id
        """
        if self.employee_id:
            self.partner_bank_id = self.employee_id.bank_account_id
            self.partner_id = self._get_employee_partner(self.employee_id)
        else:
            self.partner_bank_id = False
            self.partner_id = False
        
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super(TwAdvancePayment, self).create(vals_list)
        if 'import_file' in self._context and self._context.get('import_file') and create:
            for data in create:
                if data.type == 'advance_payment' and data.state == 'confirm':
                    data.action_validate()

        return create

    # 13: action methods
    def action_validate(self):
        """
        Override action_validate to set state to 'confirm' for Advance Payment
        after the parent's posted logic has completed.
        """
        if not self.line_dr_ids:
            self._create_line_avp()
        result = super().action_validate()
        # After parent's action_validate (which sets state to 'paid'), 
        # update state to 'confirm' for advance payment
        if self.type == 'advance_payment':
            self.write({
                'state': 'confirm',
                'confirm_uid': self.env.user.id,
                'confirm_date': self._get_default_date()
            })
        return result
    
    def action_view_payment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("tw_payment.tw_supplier_payment_action")
        context = eval(action.get('context')) if action.get('context') else {}
        context.update({
            'create':False,
        })
        action['context'] = context
        action['domain'] = [('id','in',self.payment_ids.ids)]
        return action
        
    # 14: private methods
    def _get_sequence_name(self):
        if self.type == 'advance_payment':
            seq_name = self.env['ir.sequence'].with_company(self.company_id).get_sequence_code('AVP', self.company_id.code)
        else:
            seq_name = super()._get_sequence_name()
        return seq_name
    
    def _get_validate_type(self):
        type_list = super()._get_validate_type()
        type_list.append('advance_payment')
        return type_list
    
    def unlink(self):
        for data in self:
            if data.state != 'draft':
                raise Warning('You cannot delete a document that is not in draft state')
        return super().unlink()

    # 13: Action Methods
    def action_done(self):
        return self.write({
            'state': 'done',
            'done_uid': self.env.user.id,
            'done_date': self._get_default_date()
        })
    
    # 14: Private Methods
    def _check_company(self, fnames=None):
        if fnames is None:
            fnames = {
                f for f in self._fields 
                if getattr(self._fields[f], 'check_company', False)  # safe access
            }
        # handle failed importing migration data
        # Error: "Incompatible companies on records: - “AVP/HHO/26/05/00121” belongs to company “[HHO] Head Office” and “Rekening Penerima” (partner_bank_id: '1640007588488') belongs to another company."
        fnames.discard('partner_bank_id')
        return super()._check_company(fnames=fnames)
    
    def _check_branch_config(self):
        branch_conf = self.company_id.branch_setting_id.account_setting_id
        if not branch_conf:
            raise Warning("Konfigurasi Branch Config belum dibuat !")


    def _get_default_journal_id(self):
        if self.type == 'advance_payment':
            branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
            if not branch_setting_obj.account_setting_id:
                raise Warning(
                    "Account setting is not set for branch %s.\n"
                    "- Go to the Master Branch Setting.\n"
                    "- Set the 'Account Setting' to proceed.\n"
                    "This configuration is required to create accounting entries." 
                    % self.company_id.name
                )
            if not branch_setting_obj.account_setting_id.journal_avp_id:
                raise Warning(
                        "Journal Advance Payment is not set for branch %s.\n"
                        "- Go to the Account Setting.\n"
                        "- Set the 'Journal Advance Payment'.\n"
                        "This configuration is required to create Advance Payment." 
                        % self.company_id.name
                    )
            return branch_setting_obj.account_setting_id.journal_avp_id.id
        else:
            return super()._get_default_journal_id()

    def _get_employee_partner(self, employee):
        """Resolve the real partner for an employee (not address/contact type).

        Priority:
        1. work_contact_id - The main partner linked to the employee
        2. user_id.partner_id - Partner from the employee's user account
        Raises error if no partner is found, as journal lines require a partner.
        """
        partner = employee.work_contact_id or (employee.user_id and employee.user_id.partner_id)
        if not partner:
            raise Warning(
                _("Employee '%s' tidak memiliki partner yang valid.\n"
                  "Pastikan employee memiliki Work Contact atau User Account.\n"
                  "Partner wajib diisi saat pembuatan Journal Advance Payment.") % employee.name
            )
        return partner

    def _create_line_avp(self):
        for record in self:
            if record.type == 'advance_payment':
                partner = False
                if record.employee_id:
                    partner = record._get_employee_partner(record.employee_id)
                vals = {
                    'account_id': record.journal_id.default_debit_account_id.id,
                    'name': record.description or 'Payment Amount',
                    'amount': record.amount,
                    'partner_id': partner.id if partner else partner,
                }
                if record.line_dr_ids:
                    record.line_dr_ids.write(vals)
                else:
                    line_vals_list = []
                    line_vals_list.append([0,0,vals])
                    record.line_dr_ids = line_vals_list

    def _validate_amount(self):
        super()._validate_amount()
        attachment_required = self.env['ir.config_parameter'].sudo().get_param(
            'tw_advance_payment.attachment_required', default='False'
        )
        # * bypass not required attachment while data from importing
        is_import = 'import_file' in self._context and self._context.get('import_file')
        if attachment_required == 'True' and not is_import:
            for record in self:
                if not record.attachment_ids:
                    raise Warning("Lampiran wajib diisi!")
    

            
        