# 1: imports of python lib
from datetime import datetime, timedelta, date
import requests
import json
import base64
import urllib.parse

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class ApiConfigurationInherit(models.Model):
    _inherit = "tw.api.configuration"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def get_bank_statement_popeye(self, account_number, config_obj, from_date, to_date, bank):
        """
        Fetch bank statement from Popeye API.

        :param account_number: Bank account number (str)
        :param config_obj:     tw.api.configuration record with api_type_value='popeye'
        :param from_date:      Start date (date or str YYYY-MM-DD)
        :param to_date:        End date (date or str YYYY-MM-DD)
        :return:               dict with keys 'status' (int) and 'response' (requests.Response)
        """

        dummy_data_bank_statement = self.env['ir.config_parameter'].sudo().get_param('tw_popeye_b2b_bank.dummy_data') or {}
        if dummy_data_bank_statement:
            response_data = eval(dummy_data_bank_statement)
            new_response = {'status_code': 200, 'content': response_data}
            
            # Create a fake Response object
            response = requests.models.Response()
            response.status_code = new_response['status_code']
            response._content = json.dumps(new_response['content']).encode('utf-8')  # Must be bytes

            return {'status': 1, 'response': response}
        
        url = f'{config_obj.base_url}/api/v1/bank/statement'
        token = config_obj.action_get_token_popeye(is_return_token=True)

        payload = {
            'account_number': str(account_number),
            'from_date': str(from_date),
            'to_date': str(to_date)
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        log_name = f'Popeye Bank Statement {bank.upper()}'
        request_type = 'post'
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        response_code = 400

        try:
            response = requests.post(
                url=url,
                headers=headers,
                data=json.dumps(payload)
            )
            
            response_code = response.status_code
            content = response.content
            
            jml_data = 0
            if response_code == 200:
                content = json.loads(response.content)
                data = content.get('data', [])
                jml_data = len(data) if isinstance(data, list) else 0

            params = {
                'name': log_name,
                'url': url,
                'description': f'Success Get Bank Statement Popeye {bank.upper()}',
                'ip_address': '',
                'response': content,
                'payload': payload,
                'headers': headers,
                'response_code': response_code,
                'status_code': response_code,
                'reference': '',
                'transaction_id': None,
                'api_type_id': self.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            self._create_api_log_bank(params)

            return {'status': 1, 'response': response}

        except Exception as err:
            error = f'Popeye Bank Statement {bank.upper()} Error: {err}'
            _logger.error(error)
            response = {'response': error}
            params = {
                'name': log_name,
                'url': url,
                'description': f'Failed Get Bank Statement Popeye {bank.upper()}',
                'ip_address': '',
                'response': response,
                'payload': payload,
                'headers': headers,
                'response_code': 500,
                'status_code': 500,
                'reference': '',
                'transaction_id': None,
                'api_type_id': self.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            self._create_api_log_bank(params)

            return {'status': 0, 'error': error}
        
    def schedule_popeye_statements(self, account=None, from_date=None, to_date=None, bank='bca'):
        """
        Scheduled action: fetch bank statements from Popeye for all
        active master banks configured with Popeye (api_type_value='popeye').
        Processes each bank account and creates tw.bank.mutasi records.
        """

        name = f'Popeye Bank Statement {bank.upper()}'
        request_type = 'post'
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        response_code = 400

        try:
            config_obj = self.get_api_config('popeye')
            if not config_obj:
                _logger.warning('Popeye API config not found.')
                return False
            
            where_clause = " AND ts.value = 'popeye'"
            if account:
                where_clause += f" AND b.acc_number = '{account}'"

            rows = self._get_statements_bank_data(bank=bank, where_clause=where_clause)
            if not rows:
                _logger.info('No Popeye bank accounts pending statement fetch.')
                return False
            
            for row in rows:
                master_id = row.get('id')
                account_number = row.get('acc_number')
                account_id = row.get('account_id')
                company_id = row.get('company_id')
                coa = row.get('coa')
                row_from_date = from_date or row.get('from_date')
                row_to_date = to_date or row.get('to_date')

                master_bank_obj = self.env['res.partner.bank'].browse(master_id)
                result = self.get_bank_statement_popeye(account_number, config_obj, row_from_date, row_to_date, bank)
                if result.get('status') != 1:
                    _logger.error(f"Failed to fetch statement for account {account_number}: {result.get('error', '')}")
                    continue

                response = result.get('response')
                response_code = response.status_code
                if response.status_code == 200:
                    content = json.loads(response.content)
                    data = content.get('data', [])
                    transactions = data.get('bank_statement', [])
                    if not isinstance(transactions, list):
                        error_msg = f'Unexpected data format for account {account_number}'
                        _logger.warning(error_msg)
                        response = {'response': error_msg + ' Content: ' + str(content)}
                        params = {
                            'name': 'Popeye Bank Statement Parse Error',
                            'url': f'{config_obj.base_url}/api/v1/bank/statement',
                            'description': error_msg,
                            'ip_address': '',
                            'response': response,
                            'payload': {},
                            'headers': {},
                            'response_code': response_code,
                            'status_code': response_code,
                            'reference': '',
                            'transaction_id': None,
                            'api_type_id': self.api_type_id.id,
                            'method_id': method_obj.id if method_obj else False,
                            'model_id': model_obj.id if model_obj else False
                        }
                        self._create_api_log_bank(params)
                        continue

                    # Delete pending (PEND) mutations before re-inserting fresh data
                    self._delete_pending_bank_statement(format=bank, account_id=account_id, company_id=company_id)

                    for trx in transactions:
                        transaction_date = trx.get('transaction_date', '')
                        popeye_origin = trx.get('popeye_origin', trx.get('popey_reff', ''))
                        remark = trx.get('remark', '').strip()
                        transaction_amount = trx.get('debit') or trx.get('credit') or 0

                        # Parse date string (expected: YYYY-MM-DD from Popeye)
                        transaction_date_format = False
                        if transaction_date and transaction_date != 'PEND':
                            try:
                                datetime.strptime(transaction_date, '%Y-%m-%d')
                                transaction_date_format = transaction_date
                            except ValueError:
                                _logger.warning(f'Cannot parse date: {transaction_date}')

                        vals = {
                            'remark': remark,
                            'coa': coa,
                            'date': transaction_date_format,
                            'account_id': account_id,
                            'format': bank,
                            'no_sistem': '',
                            'popeye_origin': popeye_origin,
                            'company_id': company_id
                        }

                        # Debit = D, Credit = C
                        if trx.get('debit'):
                            vals['debit'] = trx.get('debit')
                            vals['credit'] = 0
                        else:
                            vals['credit'] = trx.get('credit')
                            vals['debit'] = 0

                        # Bank IN Auto Posted
                        if (remark[0:17] == 'TRSF E-BANKING DB') and (remark[-23:] == 'KE PS TUNAS DWIPA MATRA') and coa[0:6] == '111205':
                            vals['is_posted'] = True
                        
                        params_transaction = ['PAJAK BUNGA', 'BIAYA ADM', 'BUNGA']
                        if str(remark) in params_transaction:
                            bm_obj = self.env['tw.bank.mutasi'].sudo().search([
                                ('company_id','=',company_id),
                                ('date','=',transaction_date_format),
                                ('remark','=',remark),
                                ('account_id','=',account_id),
                                ('amount','=',transaction_amount),
                                ('format','=',bank)
                            ], limit=1)
                            if not bm_obj:
                                # Bank IN Auto Posted
                                if coa[0:6] == '111205':
                                    vals['is_posted'] = True
                                bm_obj = self.env['tw.bank.mutasi'].sudo().create(vals)
                        else:
                            if str(remark) in ['CR KOREKSI BUNGA', 'DR KOREKSI BUNGA']:
                                bm_obj = self.env['tw.bank.mutasi'].sudo().search([
                                    ('company_id','=',company_id),
                                    ('date','=',transaction_date_format),
                                    ('remark','=',remark),
                                    ('account_id','=',account_id),
                                    ('amount','=',transaction_amount),
                                    ('format','=',bank)
                                ], limit=1)
                                if bm_obj:
                                    continue
                            bm_obj = self.env['tw.bank.mutasi'].sudo().create(vals)

                    # Mark bank as fetched
                    master_bank_obj.sudo().write({'last_fetch': datetime.now()})

                elif response.status_code == 404:
                    error_msg = f'No statement data found (404) for account {account_number}'
                    _logger.info(error_msg)
                    response = {'response': error_msg}
                    params = {
                        'name': 'Popeye Bank Statement 404',
                        'url': f'{config_obj.base_url}/api/v1/bank/statement',
                        'description': error_msg,
                        'ip_address': '',
                        'response': response,
                        'payload': {},
                        'headers': {},
                        'response_code': response_code,
                        'status_code': response_code,
                        'reference': '',
                        'transaction_id': None,
                        'api_type_id': self.api_type_id.id,
                        'method_id': method_obj.id if method_obj else False,
                        'model_id': model_obj.id if model_obj else False
                    }
                    self._create_api_log_bank(params)
                    master_bank_obj.sudo().write({'last_fetch': datetime.now()})

        except Exception as err:
            error = f'Exception schedule_popeye_statements: {err}'
            _logger.error(error)
            response = {'response': error}
            params = {
                'name': 'Popeye Bank Statement 500',
                'url': f'{config_obj.base_url}/api/v1/bank/statement',
                'description': error,
                'ip_address': '',
                'response': response,
                'payload': {},
                'headers': {},
                'response_code': 500,
                'status_code': 500,
                'reference': '',
                'transaction_id': None,
                'api_type_id': self.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            self._create_api_log_bank(params)

    # 14: private methods
    def _get_statements_bank_data(self, bank='bca', where_clause=''):
        query = f"""
            SELECT DISTINCT ON (b.acc_number)
                b.id
                , b.acc_number
                , b.account_id
                , b.company_id
                , aa.code_store ->> '1' AS coa
                , ((b.last_fetch + INTERVAL '7 hours')::DATE)::TEXT AS from_date
                , (CURRENT_DATE)::TEXT AS to_date
            FROM res_partner_bank b
            INNER JOIN res_bank rb ON b.bank_id = rb.id
            INNER JOIN tw_api_configuration ac ON ac.id = b.api_config_id
            INNER JOIN tw_selection ts ON ac.api_type_id = ts.id AND ts.type = 'ApiType'
            INNER JOIN account_account aa ON aa.id = b.account_id
            INNER JOIN tw_api_schedule s ON s.id = b.schedule_id
            INNER JOIN tw_api_schedule_line sd ON
            (
                (b.last_fetch + INTERVAL '7 hours')::DATE = CURRENT_DATE
                AND (b.last_fetch + INTERVAL '7 hours')::TIME < (sd.hour||':'||sd.minute)::TIME
                AND (sd.hour||':'||sd.minute)::TIME < CURRENT_TIME
            )
            OR
            (
                (b.last_fetch + INTERVAL '7 hours')::DATE < CURRENT_DATE
                AND (sd.hour||':'||sd.minute)::TIME < CURRENT_TIME
            )
            WHERE 1=1
            AND rb.name = '{bank.upper()}'
            {where_clause}
            ORDER BY b.acc_number, b.last_fetch ASC
        """
        _logger.info(f'\n\nQuery Popeye Statement:\n{query}\n\n')
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        _logger.info(f'\n\nRess Popeye Statement:\n{ress}\n\n')
        
        return ress
    
    def _delete_pending_bank_statement(self, format='bca', account_id=None, company_id=None):
        query = f"""
            DELETE FROM tw_bank_mutasi
            WHERE date IS NULL
            AND account_id = {account_id}
            AND company_id = {company_id}
            AND format = '{format}'
            AND state = 'Outstanding'
        """
        self._cr.execute(query)