# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class BankMutasiInherit(models.Model):
    _inherit = "tw.bank.mutasi"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _create_supplier_payment(self, bank_mutasi_obj, params, remark=None):
        super()._create_supplier_payment(bank_mutasi_obj, params, remark=remark)
        line_vals = {
            'account_id': params.get('account_biaya_admin_id'),
            'name': params.get('remark'),
            'type': params.get('line_type') or 'wo',
            'amount': params.get('amount')
        }
        if remark == 'PAJAK BUNGA' or remark == 'BUNGA':
            line_vals.update({'account_id': params.get('account_bunga_id')})
        vals = {
            'company_id': params.get('company_id'),
            'division': params.get('division') or 'Unit',
            'beneficiary_company_id': params.get('beneficiary_company_id'),
            'partner_type': params.get('partner_type'),
            'partner_id': params.get('partner_id'),
            'amount': params.get('amount'),
            'journal_id': params.get('journal_id'),
            'narration': params.get('remark'),
            'currency_id': params.get('currency_id'),
            'account_id': params.get('account_id'),
            'type': params.get('type') or 'supplier_payment',
            'payment_type': params.get('payment_type') or 'outbound',
            'line_wo_ids': [
                [0, False, line_vals]
            ]
        }
        supplier_payment_obj = self.env['tw.account.payment'].suspend_security().create(vals)
        if remark == 'BUNGA':
            supplier_payment_obj.action_validate()
        else:
            supplier_payment_obj.action_request_approval()
            supplier_payment_obj.action_approval()
            supplier_payment_obj.sudo().action_post()
        bank_mutasi_obj.no_sistem = supplier_payment_obj.name

        return supplier_payment_obj
    
    def _create_bank_transfer(self, bank_mutasi_obj, params):
        super()._create_bank_transfer(bank_mutasi_obj, params)
        vals = {
            'company_id': params.get('company_id'),
            'division': params.get('division') or 'Unit',
            'journal_id': params.get('journal_id'),
            'description': params.get('description'),
            'amount': params.get('amount'),
            'line_ids': [
                [0, False, {
                    'branch_destination_id': params.get('branch_destination_id'),
                    'payment_to_id': params.get('payment_to_id'),
                    'description': params.get('description'),
                    'amount': params.get('amount')
                }]
            ]
        }

        bank_transfer_obj = self.env['tw.bank.transfer'].suspend_security().create(vals)
        bank_transfer_obj.action_request_approval()
        bank_transfer_obj.action_approval()
        bank_transfer_obj.action_confirm()
        bank_mutasi_obj.no_sistem = bank_transfer_obj.name

        return bank_transfer_obj