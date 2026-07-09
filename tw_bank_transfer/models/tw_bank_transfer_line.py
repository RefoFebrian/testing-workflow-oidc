
# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwBankTransferLine(models.Model): 
    _name = "tw.bank.transfer.line"
    _description = 'Bank Transfer Line'

    
    # 7: defaults methods

    # 8: fields
    name = fields.Char(string="Name",readonly=True)
    description = fields.Char(string="Description")
    amount = fields.Float('Amount')
    
    
    # 9: relation fields
    # TODO: buat domain khusus untuk branch_destination_id reference ke teds
    branch_destination_id = fields.Many2one('res.company', string='Branch Destination', required=True)   
    payment_to_id = fields.Many2one('account.journal',string="Bank",domain="[('company_id', '=',branch_destination_id)]")
    bank_transfer_id = fields.Many2one('tw.bank.transfer',string="Bank Transfer")
    reimbursement_id = fields.Many2one('tw.reimbursement.petty.cash',domain="[('state','=','approved'),('company_id', '=',branch_destination_id)]", string="Reimbursed No")
    
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('reimbursement_id',False):
                obj = self.env['tw.reimbursement.petty.cash'].browse(vals['reimbursement_id'])
                vals['amount'] = obj.amount_total

        return super(TwBankTransferLine,self).create(vals)

    
    def write(self,vals):
        if vals.get('reimbursement_id',False):
            obj = self.env['tw.reimbursement.petty.cash'].browse(vals['reimbursement_id'])
            vals['amount'] = obj.amount_total

        return super(TwBankTransferLine,self).write(vals)


    @api.onchange('branch_destination_id')
    def branch_destination_change(self):
        if not self.bank_transfer_id.description \
            or not self.bank_transfer_id.company_id  \
            or not self.bank_transfer_id.journal_id :
                raise Warning("Sebelum menambah detil transaksi,\n harap isi data header terlebih dahulu.")


        dom = {}
        rekap_journal_id = []
        journal_id = self.env['account.journal'].sudo().search([
            ('company_id.code', '=', self.branch_destination_id.code),
            ('type', 'in', ('cash', 'bank', 'pettycash'))
        ])

        if journal_id :
            for x in journal_id :
                rekap_journal_id.append(x.id)            
            dom['payment_to_id'] = [('id', 'in', (rekap_journal_id))]
        
        else :
            dom['payment_to_id'] = [
                ('company_id.code', '=', self.branch_destination_id.code),
                ('type', 'in', ('cash', 'bank', 'pettycash'))
            ]

        self.description = self.bank_transfer_id.description
        if not self.reimbursement_id :
          self.payment_to_id = False

        return { 'domain': dom }
   
    @api.onchange('reimbursement_id','branch_destination_id','amount')
    def change_reimbursement(self):
        if self.reimbursement_id :
            dupl = self.search([
                ('reimbursement_id','=',self.reimbursement_id.id),
                ('bank_transfer_id.state','!=','cancel'),
            ],limit=1)
            if dupl:
                return {
                    'value': {'reimbursement_id': False},
                    'warning': {
                        'title':'Perhatian!',
                        'message':'Reimbursed No %s sudah ada di %s' % (
                            self.reimbursement_id.name,dupl.bank_transfer_id.name
                        ),
                    },
                }
            self.branch_destination_id = self.reimbursement_id.company_id.id
            self.payment_to_id = self.reimbursement_id.journal_id.id
            self.amount = self.reimbursement_id.amount_total
   
    @api.onchange('amount')
    def change_amount(self):
        if self.amount and self.reimbursement_id :
            self.amount = self.reimbursement_id.amount_total
