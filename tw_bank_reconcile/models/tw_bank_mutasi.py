# 1: imports of python lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.exceptions import ValidationError

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class BankMutasi(models.Model):
    _name = "tw.bank.mutasi"
    _description = 'Bank Mutasi'

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    # 8: fields
    name = fields.Char(string='Name')
    remark = fields.Char(string='Remark')
    time = fields.Char(string='Time')
    teller = fields.Char(string='Teller')
    coa = fields.Char(string='COA')
    no_sistem = fields.Char(string='No Sistem')
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
    amount = fields.Float(string='Amount')
    saldo = fields.Float(string='Saldo')
    format = fields.Selection([
        ('bca', 'BCA'),
        ('bri', 'BRI'),
        ('bni', 'BNI'),
        ('mandiri', 'Mandiri'),
        ('update', 'Update Bank Mutasi')
    ], string='Format')
    state = fields.Selection([
        ('Outstanding', 'Outstanding'),
        ('Reconciled', 'Reconciled'),
        ('Auto Reconcile', 'Auto Reconcile')
    ], string='State', default='Outstanding')
    date = fields.Date(string='Date')
    date_upload= fields.Date(string='Tanggal Upload', default=_get_default_date)
    effective_date_reconcile = fields.Date(string='Effective Date Reconcile')
    reconciled = fields.Boolean(string='Reconciled', default=False)
    checked = fields.Boolean(string='Checked', default=False)
    is_posted = fields.Boolean(string='Auto Posted ?')

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch')
    account_id = fields.Many2one(comodel_name='account.account', string='Account')
    journal_id = fields.Many2one(comodel_name='account.journal', string='Journal', domain="[('company_id','parent_of',company_id)]")
    bank_reconcile_id = fields.Many2one(comodel_name='tw.bank.reconcile', string='Bank Reconcile')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def _auto_init(self):
        res = super(BankMutasi, self)._auto_init()
        self._cr.execute("SELECT indexname FROM pg_indexes WHERE indexname = 'tw_bank_mutasi_branch_date_no_sistem_index'")
        if not self._cr.fetchone():
            self._cr.execute('CREATE INDEX tw_bank_mutasi_branch_date_no_sistem_index ON tw_bank_mutasi USING btree (company_id, date, no_sistem)')
        return res
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            credit = 0
            debit = 0
            if vals.get('credit'):
                credit = float(vals['credit'])
                vals['debit'] = 0
            if vals.get('debit'):
                debit = float(vals['debit'])
                vals['credit'] = 0
            amount = debit + credit
            vals['amount'] = amount
            if vals.get('date'):
                branch_obj = self.env['res.company'].sudo().browse(vals['company_id'])
                name = self.env['ir.sequence'].get_sequence_code('BM', branch_obj.code)
                vals['name'] = name

        return super(BankMutasi, self).create(vals_list)

    # 13: action methods
    def action_bank_mutasi_tree(self):
        domain = []
        name = 'Bank Mutasi'
        list_view_id = self.env.ref('tw_bank_reconcile.tw_bank_mutasi_list_view').id
        form_view_id = self.env.ref('tw_bank_reconcile.tw_bank_mutasi_form_view').id
        search_view_id = self.env.ref('tw_bank_reconcile.tw_bank_mutasi_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.bank.mutasi',
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'domain': domain,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1,
                'search_default_outstanding': 1,
                'search_default_pending': 1,
                'search_default_group_by_account_id': 1
            },
        }
    
    def action_reconcile(self):
       self.auto_reconcile_scheduled()

    def auto_reconcile_scheduled(self):
        datas = self.search([
            ('state','=','Outstanding'),
            ('no_sistem','!=',''),
            ('checked','=',False)
        ], limit=30)
        self.auto_reconcile(datas)

    def auto_reconcile(self, datas):
        for data in datas:
            data = self.browse(data.id)
            bank_reconcile_model = self.env['tw.bank.reconcile']
            aml = self.env['account.move.line']
            if data:
                debit = data.debit
                credit = data.credit
                no_sistem = str(tuple(data.no_sistem.split('|'))).replace(',)', ')')
                coa = data.account_id.id
                query = f"""
                    SELECT
                        id
                        , debit
                        , credit
                    FROM account_move_line
                    WHERE ref IN {no_sistem} AND account_id = {coa}
                """
                self.env.cr.execute(query)
                ress = self.env.cr.dictfetchall()
                if ress:
                    rk_balance = data.debit - data.credit
                    journal_balance = 0
                    journal_ids = []
                    for res in ress:
                        journal_ids.append(res['id'])
                        journal_balance += res['debit'] - res['credit']

                    if abs(journal_balance + rk_balance) <= 10:
                        vals = {
                            'company_id': data.company_id.id,
                            'state': 'Auto Reconcile',
                            'move_line_ids': [[6, False, journal_ids]],
                            'account_id':data.account_id.id,
                            'bank_mutasi_ids': [[6, False, [data.id]]],
                        }
                        bank_reconcile_obj = bank_reconcile_model.suspend_security().create(vals)
                        bank_reconcile_obj.action_confirm()
                    else:
                        data.write({'checked': True})
                else:
                    data.write({'checked': True})

    # 14: private methods