# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwBankTransfer(models.Model):
    _name = "tw.bank.transfer"
    _description = 'Bank Transfer'
    _order = "id desc"
     
    # 7: defaults methods
    @api.depends('line_ids.amount','bank_fee')
    def _compute_amount(self):
        self.ensure_one()
        self.amount_total = sum(line.amount for line in self.line_ids) + self.bank_fee
    
    def _get_default_date(self):
        return date.today()
             
    # 8: fields
    name = fields.Char(string="Name",readonly=True,default='')
    amount = fields.Float('Amount')
    state= fields.Selection([
        ('draft', 'Draft'),
        ('posted','Posted'),
        ('cancel','Cancelled')], string='State', readonly=True,default='draft')
    date = fields.Date(string="Date",required=True,readonly=True,default=_get_default_date)
    description = fields.Text(string="Description")
    bank_fee = fields.Float(string='Bank Transfer Fee',digits='Account')
    amount_total = fields.Float(string='Total Amount',digits='Account', store=True, readonly=True, compute='_compute_amount',)
    note = fields.Text(string="Note")
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    journal_type = fields.Selection(related='journal_id.type',string="Journal Type")
    email = fields.Char(string="Email")
    
    account_number = fields.Char('Account Number')
    account_holder = fields.Char('Account Holder')
    transfer_note = fields.Char('Transfer Note',compute='_compute_transfer_note',precompute=True,store=True)

    # used to know whether the field `partner_bank_id` needs to be displayed/required or not in the payments form views
    show_partner_bank_account = fields.Boolean(compute='_compute_show_require_partner_bank')
    show_account_number = fields.Boolean(compute='_compute_show_require_partner_bank')
    require_partner_bank_account = fields.Boolean(compute='_compute_show_require_partner_bank')
    require_account_number = fields.Boolean(compute='_compute_show_require_partner_bank')
    
    # Audit Trail
    confirm_uid = fields.Many2one('res.users',string="Posted by")
    confirm_date = fields.Datetime('Posted on')
    cancel_uid = fields.Many2one('res.users',string="Cancelled by")
    cancel_date = fields.Datetime('Cancelled on')

    # 9: relation fields
    payment_method_id = fields.Many2one('account.payment.method', string="Payment Method", help="Real 'payment method', this field is used for selecting a payment method not like the previous odoo version when it was used to select a Journal", default=lambda self: self.env['account.payment.method'].search([('payment_type','=','outbound')], limit=1))
    bank_id = fields.Many2one('res.bank', string='Bank')
    company_id = fields.Many2one('res.company', string='Branch', required=True, default=lambda self: self.env.company)
    journal_id = fields.Many2one('account.journal',string="Journal",domain="[('company_id','parent_of',company_id),('type','in',['cash','bank'])]")
    move_id = fields.Many2one('account.move', string='Account Entry', copy=False)
    move_ids = fields.One2many(related='move_id.line_ids', string='Journal Items', readonly=True)
    line_ids = fields.One2many('tw.bank.transfer.line','bank_transfer_id',string="Bank Transfer Line")
    period_id = fields.Many2one('tw.account.period', string="Period", related='move_id.period_id', store=True, readonly=True)
    account_id = fields.Many2one(related='journal_id.default_debit_account_id',string='Account')
    partner_id = fields.Many2one('res.partner',string='Partner')
    partner_bank_id = fields.Many2one('res.partner.bank', string="Rekening Penerima",domain="[('id', 'in', available_partner_bank_ids)]",ondelete='restrict')

    available_account_ids = fields.Many2many(comodel_name='account.account',compute='_compute_available_account_ids')
    available_partner_bank_ids = fields.Many2many(comodel_name='res.partner.bank',compute='_compute_available_partner_bank_ids',)
    reconcile_ids = fields.One2many('tw.bank.transfer.reconcile.line','bank_transfer_id',string="Reconcile Items")
    
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('journal_id')
    def onchange_amount(self):
        if self.journal_id:
            self.amount = 0
            self.reconcile_ids = False
            if self.journal_id.type == 'cash' : 
                self.amount = self.journal_id.default_debit_account_id.current_balance

    @api.onchange('partner_bank_id')
    def _onchange_partner_bank_id(self):
        if self.partner_bank_id:
            self.account_number = self.partner_bank_id.acc_number
            self.account_holder = self.partner_bank_id.acc_holder_name
        else:
            self.account_number = False
            self.account_holder = False
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.partner_bank_id = False
        
    
    @api.onchange('payment_method_id')
    def _onchange_payment_method_id(self):
        self.partner_bank_id = False
        self.bank_id = False
        self.account_number = False
        self.account_holder = False

    @api.depends('company_id')
    def _compute_available_account_ids(self):
        for record in self:
            domain = [('id', 'in', [])]
            if record.company_id:
                domain = ['|', ('company_ids', 'in', record.company_id.id), ('company_ids', 'parent_of', record.company_id.id)]
            payment_type = 'bank_transfer'            
            account_filter_domain = self.env['tw.account.filter'].get_account_domain(payment_type)
            if account_filter_domain:
                domain += account_filter_domain
            record.available_account_ids = self.env['account.account'].search(domain)

    @api.depends('payment_method_id')
    def _compute_show_require_partner_bank(self):
        """ Computes if the destination bank account must be displayed in the payment form view. By default, it
        won't be displayed but some modules might change that, depending on the payment type."""
        for payment in self:
            if payment.payment_method_id.is_require_bank_account:
                payment.show_partner_bank_account = True
            else:
                payment.show_partner_bank_account = False
            
            if payment.payment_method_id.is_require_account_number:
                payment.show_account_number = True
            else:
                payment.show_account_number = False
            
            payment.require_partner_bank_account = payment.state == 'draft' and payment.show_partner_bank_account
            payment.require_account_number = payment.state == 'draft' and payment.show_account_number

    @api.depends('journal_id','account_number','account_holder')
    def _compute_transfer_note(self):
        for record in self:
            transfer_note = ''
            if record.journal_id:
                transfer_note += record.journal_id.bank_account_id.code if record.journal_id.bank_account_id.code else ''
                transfer_note += ' '
            if record.account_number:
                transfer_note += record.account_number
                transfer_note += ' '
            if record.account_holder:
                transfer_note += record.account_holder
                transfer_note += ' '
            
            record.transfer_note = transfer_note

    @api.depends('partner_id', 'company_id')
    def _compute_available_partner_bank_ids(self):
        for pay in self:
            pay.available_partner_bank_ids = pay.partner_id.bank_ids\
                    .filtered(lambda x: x.company_id.id in (False, pay.company_id.id))._origin
    
    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            journal = self.env['account.journal'].browse(vals['journal_id'])
            company_id = self.env['res.company'].browse(vals['company_id'])
            vals['name'] = self.env['ir.sequence'].get_sequence_code('BT',company_id.code) 
            vals['date'] = self._get_default_date()

        return super(TwBankTransfer, self).create(vals_list)
    
    def unlink(self):
        for item in self:
            if item.state != "draft":
                raise Warning("Bank Transfer sudah diproses, data tidak bisa didelete !")
        return super(TwBankTransfer, self).unlink()     

    # 13: action methods
    
    def action_confirm(self):
        self._validate_bank_transfer()
        ada=0
        message=''
        for inv in self.line_ids:
            inv.reimbursement_id
            if inv.reimbursement_id.state!='paid':
                self.write(
                  {
                    'date':self._get_default_date(),
                    'state':'posted',
                    'confirm_uid':self._uid,
                    'confirm_date':datetime.now()
                   })
                if self.journal_id.type == 'cash' :
                    if round(self.amount,2) > round(self.journal_id.default_debit_account_id.current_balance,2):
                        raise Warning("Saldo kas tidak mencukupi !")

                res = self._create_account_move()
     
                return True  
            else:
                message += "Nomor Reimburse %s sudah %s. \r\n" % (inv.reimbursement_id.name,inv.reimbursement_id.state)
                ada +=1
        if ada>0:
            raise Warning('Perhatian ! \n %s' %(message))
        self.write({
            'state':'posted',
            'confirm_uid':self._uid,
            'confirm_date':datetime.now()
        })
        
    def action_cancel(self):
        self.write({'state':'cancel','cancel_uid':self._uid,'cancel_date': self._get_default_date()})
        return True
    
    def action_print_payment_request(self):
        self.ensure_one()
        return self.env.ref('tw_bank_transfer.action_report_tw_bank_transfer_payment_request_report').report_action(self.id)

    # 14: private methods
    def _validate_bank_transfer(self):
        for bt in self:
            if bt.amount_total <= 0:
                raise Warning('The amount cannot be less than or equal to 0')
            bt._check_amount()
            bt._check_double_reimbursement()
    
    def _check_double_reimbursement(self):
        self.ensure_one()
        for line in self.line_ids:
            if line.reimbursement_id:
                dupl = line.search([
                    ('id','!=',line.id),
                    ('reimbursement_id','=',line.reimbursement_id.id),
                    ('bank_transfer_id.state','!=','cancel'),
                ],limit=1)
                if dupl:
                    raise Warning('Perhatian !\nReimbursed No %s sudah ada di %s' % (line.reimbursement_id.name,dupl.bank_transfer_id.name))
                
    def _check_amount(self):
        for bank in self:
            if round(bank.amount_total,2) != round(bank.amount,2):           
                raise Warning('Total Amount tidak sesuai, mohon cek kembali data Anda. (Total Amount: %s, Amount: %s)' % (bank.amount_total, bank.amount))

    def _check_double_entries(self):
        if self.id == 0:
            ids = [0]
        self.move_line_id
        ids = str(tuple(ids)).replace(',)', ')')
        move_line_ids = str(tuple(move_line_ids)).replace(',)',')')
        query = """
            select btr.name, btr.amount_original, bt.name
            from tw_bank_transfer bt 
            inner join tw_bank_transfer_reconcile_line btr on bt.id = btr.bank_transfer_id
            where bt.state in ('draft', 'waiting_for_approval', 'confirmed', 'app_approve')
            and (bt.id not in (%s) or %s)
            and btr.move_line_id in %s
        """ % (ids, '1=1' if ids == [0] else '1=0', move_line_ids)
        cr.execute(query)
        data = cr.fetchall()
        if len(data) > 0:
            message = ""
            for x in data :
                message += "Detil %s (%s) sudah ditarik di nomor %s. \r\n" % (x[0], x[1], x[2])
            raise Warning('Perhatian !', message)

    def _create_account_move(self):
        if self.move_id:
            raise Warning(_("Bank Transfer already posted or Journal Entry already created."))
        self._check_branch_config()
        currency_id = self.company_id.currency_id.id
        move_vals = {
            'move_type': 'entry',
            'ref': self.name,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'division': self.division,
            'currency_id': currency_id,
            'partner_bank_id': False,
            'line_ids': [
                Command.create(line_vals)
                for line_vals in self._prepare_move_line_default_vals()
            ],
        }
        if self.name:
            move_vals['name'] = self.name
        move_created = self.env['account.move'].create([move_vals])
        
        move_created.sudo().action_post()
        
        self.move_id = move_created.id
    
    def _prepare_move_line_default_vals(self):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        period_ids = self.env['tw.account.period']._get_current_periods()
        currency_id = self.company_id.currency_id.id
        branch_conf = self.company_id.branch_setting_id.account_setting_id or branch.branch_setting_id.account_setting_id
        line_vals_list = []       
        taxes = {}

        # * Set Account
        credit_account_id = self.journal_id.default_credit_account_id.id
        debit_account_id = self.journal_id.default_debit_account_id.id
        bank_fee_account_id = branch_conf.account_bank_transfer_fee_id.id
        if not credit_account_id or not debit_account_id:
            raise Warning("Account Credit / Debit pada %s belum diisi!" %(self.journal_id.name))
        line_vals_list.append({
                    'name': self.description,
                    'account_id': credit_account_id,
                    'period_id': period_ids.id,
                    'date': self._get_default_date(),
                    'debit': 0.0,
                    'credit': self.amount,
                    'amount_currency': -self.amount,
                    'company_id': self.company_id.id,
                    'division': self.division,
                    'currency_id': currency_id,
                    'date_maturity': self._get_default_date(),
                })
        if self.bank_fee > 0:
            line_vals_list.append({
                'name': 'Bank Transfer Fee',
                'date_maturity': self._get_default_date(),
                'amount_currency': self.bank_fee,
                'currency_id': currency_id,
                'period_id': period_ids.id,
                'debit': self.bank_fee,
                'credit': 0.0,
                'account_id': bank_fee_account_id,
                'company_id': self.company_id.id,
                'division': self.division,
                'currency_id': currency_id,
                'date_maturity': self._get_default_date(),
            })
        for record in self.line_ids:
            line_vals_list.append({
                    'name': record.description,
                    'account_id': record.payment_to_id.default_debit_account_id.id,
                    'period_id': period_ids.id,
                    'date': self._get_default_date(),
                    'debit': record.amount,
                    'credit': 0.0,
                    'amount_currency': record.amount,
                    'company_id': record.branch_destination_id.id,
                    'division': self.division,
                    'currency_id': currency_id,
                    'date_maturity': self._get_default_date(),
            })  

            if record.reimbursement_id:
                record.reimbursement_id.write({'state':'paid','bank_transfer_id':self.id})               
      
        return line_vals_list

    def _check_branch_config(self):
        if not self.company_id.branch_setting_id:
            raise Warning("Konfigurasi Branch Setting belum dibuat di Company Setting !")
        if not self.company_id.branch_setting_id.account_setting_id:
            raise Warning("Konfigurasi Account Setting belum dibuat di Branch Setting !")
        branch_conf = self.company_id.branch_setting_id.account_setting_id
        if not branch_conf:
            raise Warning("Konfigurasi Account Settlement belum dibuat di Account Setting !")
        else:
            if not branch_conf.account_bank_transfer_fee_id:
                raise Warning("Konfigurasi Account Bank Transfer Fee belum di isi di Account Setting !") 

            for data in self.line_ids:
                if not data.payment_to_id.default_credit_account_id:
                    raise Warning("Account Credit Bank Transfer Fee belum diisi dalam journal %s!" %(data.payment_to_id.default_credit_account_id.name))
                if not data.payment_to_id.default_debit_account_id:
                    raise Warning("Account Debit Bank Transfer Fee belum diisi dalam journal %s!" %(data.payment_to_id.default_debit_account_id.name))

    def company_id_change(self,company_id):
        value = {}
        if company_id :
            value['journal_id'] = False
        
        return {'value':value}
