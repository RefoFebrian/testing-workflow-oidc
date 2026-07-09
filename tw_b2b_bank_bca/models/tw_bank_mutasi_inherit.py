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
    def action_schedule_auto_posting_bca(self):
        self.schedule_auto_posting_bca(self.id)

    def schedule_auto_posting_bca(self, bm_id=False):
        ress = self._get_auto_posting_bca_data(bm_id)
        for res in ress:
            remark = res.get('remark')
            company_id = res.get('company_id')
            journal_id = res.get('journal_id')
            journal_code = res.get('journal_code')
            amount = res.get('amount')
            rk_id = res.get('rk_id')
            partner_id = res.get('partner_id')
            payment_to_id = res.get('payment_to_id')
            payment_to_mml_id = res.get('payment_to_mml_id')
            account_id = res.get('account_id')
            account_biaya_admin_id = res.get('account_biaya_admin_id')
            account_bunga_id = res.get('account_bunga_id')
            company_id = res.get('company_id')
            currency_id = res.get('currency_id')
            bank_mutasi_obj = self.browse(rk_id)

            vals = {
                'company_id': company_id,
                'division': 'Unit',
                'journal_id': journal_id,
                'description':  remark,
                'amount': amount,
                'branch_destination_id': company_id,
                'payment_to_id': payment_to_id
            }
            if ((remark[0:17] == 'TRSF E-BANKING DB') and (remark[-23:] == 'KE PS TUNAS DWIPA MATRA')) or ((remark[0:17] == 'TRSF E-BANKING DB') and (remark[-23:] == 'KE SP TUNAS DWIPA MATRA')):
                branch_destination_code = 'HHO'
                if (remark[0:17] == 'TRSF E-BANKING DB') and (remark[-23:] == 'KE SP TUNAS DWIPA MATRA'):
                    # * khusus untuk DLR. PAYMENT TO ID NYA ke MML
                    if journal_code == 'BK01DLR':
                        branch_destination_code = 'MML'
                        payment_to_id = payment_to_mml_id
                        vals.update({'payment_to_id': payment_to_id})
                branch_destination_id = self._get_branch_dest_id(branch_destination_code)
                vals.update({'branch_destination_id': branch_destination_id})

                bank_transfer_obj = self._create_bank_transfer(bank_mutasi_obj, vals)
            elif remark in ('BIAYA ADM', 'PAJAK BUNGA', 'BUNGA'):
                del vals['description']
                del vals['branch_destination_id']
                del vals['payment_to_id']
                vals.update({
                    'beneficiary_company_id': company_id,
                    'partner_type': 'customer',
                    'partner_id': partner_id,
                    'remark': remark,
                    'currency_id': currency_id,
                    'account_id': account_id,
                    'type': 'supplier_payment',
                    'payment_type': 'outbound',
                    'account_biaya_admin_id': account_biaya_admin_id,
                    'account_bunga_id': account_bunga_id,
                    'line_type': 'wo'
                })
                if remark == 'BUNGA':
                    vals.update({
                        'type': 'customer_payment',
                        'payment_type': 'inbound'
                    })

                supplier_payment_obj = self._create_supplier_payment(bank_mutasi_obj, vals, remark=remark)
        
        self.action_reconcile()

    # 14: private methods
    def _get_branch_dest_id(self, code):
        branch_destination_obj = self.env['res.company'].sudo().search([('code','=',code)], limit=1)
        if not branch_destination_obj:
            raise Warning(f"Branch Destination {code} doesn't exist !")
        
        return branch_destination_obj.id

    def _get_auto_posting_bca_data(self, bm_id=False):
        additional_where = ''
        if str(bm_id).isdigit():
            additional_where = f' AND bm.id = {bm_id}'

        hho_company_id = self.env['res.company'].sudo().get_default_ho_branch().id
        mml_company_id = self.env['res.company'].sudo().get_default_main_dealer().id

        query = f"""
            SELECT 
                TRIM(bm.remark) AS remark
                , bm.name AS no_rk
                , bm.id AS rk_id
                , bm.no_sistem
                , bm.amount
                , bm.company_id
                , aj.id AS journal_id
                , aj.code AS journal_code
                , aa.id AS account_id
                , (SELECT id FROM account_journal WHERE code = 'BK01H' AND company_id = {hho_company_id}) AS payment_to_id
                , (SELECT id FROM account_journal WHERE code = 'BK05M' AND company_id = {mml_company_id}) AS payment_to_mml_id
                , (SELECT id FROM res_partner WHERE code = 'BCA') AS partner_id
                , (SELECT id FROM account_account WHERE code_store ->> '1' = '812102') AS account_biaya_admin_id
                , (SELECT id FROM account_account WHERE code_store ->> '1' = '711102') AS account_bunga_id
                , COALESCE(aj.company_id, b.parent_id) AS company_id
                , COALESCE(aj.currency_id, c.currency_id) AS currency_id
            FROM tw_bank_mutasi bm
            INNER JOIN res_company b ON bm.company_id = b.id
            INNER JOIN account_account aa ON bm.account_id = aa.id
            INNER JOIN account_journal aj ON aj.default_debit_account_id = aa.id
            LEFT JOIN res_company c ON aj.company_id = c.id
            WHERE 1=1
            AND bm.name IS NOT NULL
            AND bm.state = 'Outstanding'
            AND bm.is_posted = True
            AND (bm.no_sistem IS NULL OR bm.no_sistem = '')
            AND bm.format = 'bca'
            {additional_where}
            ORDER BY bm.remark ASC
            LIMIT 10
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        
        return ress
    
    def _create_supplier_payment(self, bank_mutasi_obj, params, remark=None):
        return bank_mutasi_obj
    
    def _create_bank_transfer(self, bank_mutasi_obj, params):
        return bank_mutasi_obj