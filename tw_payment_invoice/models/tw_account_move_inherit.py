# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.fields import Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    # 7: defaults methods

    # 8: fields
    is_auto_payment_invoice = fields.Boolean(string='Is Auto Payment Invoice', compute='_compute_is_auto_payment_invoice')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('payment_reference')
    def _compute_is_auto_payment_invoice(self):
        for rec in self:
            rec.is_auto_payment_invoice = False
            if rec.payment_reference:
                if ('WO' in rec.payment_reference or 'SL' in rec.payment_reference or 'DP' in rec.payment_reference):
                    rec.is_auto_payment_invoice = True

    # 12: override methods

    # 13: action methods
    def action_auto_create_ar_payment_manual(self):
        return self.action_auto_create_ar_payment()
    
    def action_auto_create_ar_payment_qris(self):
        return self.action_auto_create_ar_payment(payment_method_type='qris')
    
    def action_auto_create_ar_payment_va(self):
        return self.action_auto_create_ar_payment(payment_method_type='va')
        
    def action_auto_create_ar_payment(self, payment_method_type='manual'):
        is_process_auto_create_ar_payment = False
        if self.ref and self.payment_reference:
            if 'WO' in self.ref and 'WO' in self.payment_reference:
                is_process_auto_create_ar_payment = True
            elif 'SO' in self.ref and ('SL' in self.payment_reference or 'DP' in self.payment_reference):
                is_process_auto_create_ar_payment = True
        if is_process_auto_create_ar_payment:
            result_validation, datas = self._check_validation_auto_create_ar_payment(payment_method_type)
            if not result_validation:
                values = self._prepare_values_auto_create_ar_payment(datas)
                try:
                    ar_obj = self.env['tw.account.payment'].suspend_security().with_company(self.company_id).create(values)
                    return ar_obj
                except Exception as err:
                    raise Warning(f'Gagal create Auto Customer Payment (AR) untuk invoice : {self.name} karena {err}!')
            else:
                raise Warning(f"Customer Payment (AR) atas invoice {self.name} sudah dibuat di {datas.get('name')} !")
        else:
            raise Warning(f"Tidak bisa Auto Create Customer Payment (AR) atas invoice {self.name} ini!")
    
    # 14: private methods
    def _check_validation_auto_create_ar_payment(self, payment_method_type):
        datas = {}
        if self.payment_state == 'paid':
            raise Warning(f'Invoice sudah lunas!')
        
        invoice_obj = self.env['account.move.line'].sudo().search([
            ('ref','=',self.ref),
            ('debit','!=',0),
            ('division','=',self.division),
            ('partner_id','=',self.partner_id.id),
            ('display_type','=','payment_term'),
            ('reconciled','=',False),
            ('full_reconcile_id','=',False)
        ])
        if not invoice_obj:
            raise Warning(f'Account move tidak ditemukan!')
        
        ar_obj = self.env['tw.account.payment.line'].sudo().search([
            ('move_line_id','=',invoice_obj.id),
            ('company_id','=',self.company_id.id),
            ('partner_id','=',self.partner_id.id),
            ('payment_id.state','!=','canceled')
        ], limit=1)
        if not ar_obj:
            reconciled = invoice_obj._check_reconciled()
            if reconciled:
                raise Warning(f'Account move sudah reconciled!')
            
            payment_method = ['bank', 'cash']
            journal_obj = self.env['account.journal'].sudo().search([
                '|',
                ('company_id','=',self.company_id.id),
                ('company_id','=',self.company_id.parent_id.id),
                ('type','in',payment_method)
            ], limit=1)
            if not journal_obj:
                raise Warning(f'Journal tipe {str(payment_method)} pada {self.company_id.name} tidak ditemukan!')
            
            method = 'manual payment'
            method_name = '%'+method+'%'
            if payment_method_type == 'qris':
                method = 'qris'
                method_name = '%'+method+'%'
            elif payment_method_type == 'va':
                method = 'virtual account'
                method_name = '%'+method+'%'
            payment_method_obj = self.env['account.payment.method'].sudo().search([
                ('payment_type','=','inbound'),
                ('name','=ilike',method_name)
            ], limit=1)
            if not payment_method_obj:
                raise Warning(f"Payment Method {method.upper() if payment_method_type == 'qris' else method.title()} tidak ditemukan!")
            
            datas.update({
                'invoice_obj': invoice_obj,
                'journal_obj': journal_obj,
                'payment_method_type': payment_method_type,
                'payment_method_obj': payment_method_obj
            })

            return False, datas
        else:
            datas.update({'name': ar_obj.payment_id.name})

            return True, datas
        
    def _prepare_values_auto_create_ar_payment(self, datas):
        invoice_obj = datas.get('invoice_obj')
        journal_obj = datas.get('journal_obj')
        payment_method_type = datas.get('payment_method_type')
        payment_method_obj = datas.get('payment_method_obj')

        remaining_amount = self.amount_total
        currency = self.env.user.company_id.currency_id or journal_obj.company_id.currency_id
        
        if invoice_obj.currency_id and currency == invoice_obj.currency_id:
            amount_original = abs(invoice_obj.amount_currency)
            amount_unreconciled = abs(invoice_obj.amount_residual)
        else:
            # always use the amount booked in the company currency as the basis of the conversion into the voucher currency
            amount_original = currency.round(invoice_obj.credit or invoice_obj.debit or 0.0)
            amount_unreconciled = currency.round(abs(invoice_obj.amount_residual))
    
        line_cr_ids = [
            Command.create({
                'move_line_id': invoice_obj.id,
                'account_id': invoice_obj.account_id.id,
                'amount_original': amount_original,
                'amount_unreconciled': amount_unreconciled,
                'is_reconciled': True,
                'amount': invoice_obj and min(abs(remaining_amount), amount_unreconciled) or 0.0
            })
        ]

        payment_method_line_obj = False
        if payment_method_type == 'qris':
            payment_method_line_obj = self.env['account.payment.method.line'].sudo().search([
                ('name','=ilike','%astrapay%'),
                ('journal_id','=',journal_obj.id)
            ], limit=1)
            if not payment_method_line_obj:
                raise Warning(f'Payment Method QRIS tidak ditemukan!')
        elif payment_method_type == 'va':
            payment_method_line_obj = self.env['account.payment.method.line'].sudo().search([
                ('name','=ilike','%bca%'),
                ('journal_id','=',journal_obj.id)
            ], limit=1)
            if not payment_method_line_obj:
                raise Warning(f'Payment Method Virtual Account tidak ditemukan!')

        values = {
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id,
            'division': self.division,
            'type': 'customer_payment',
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'memo': f'Auto create Customer Payment (AR) from Invoice [{self.name}]',
            'payment_method_id': payment_method_obj.id,
            'journal_id': journal_obj.id,
            'amount': invoice_obj and min(abs(remaining_amount), amount_unreconciled) or 0.0,
            'line_cr_ids': line_cr_ids
        }
        if payment_method_type in ('qris', 'va'):
            values.update({'payment_method_line_id': payment_method_line_obj.id})

        return values