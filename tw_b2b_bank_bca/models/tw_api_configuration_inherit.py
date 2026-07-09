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
    def action_get_token_bca_manual(self):
        return self.get_token_bca(self)

    def get_token_bca(self, config_obj):
        client = config_obj.client_id
        secret = config_obj.client_secret
        api_url = self.env['tw.api.url'].sudo()._get_api_url_by_type(config_obj, 'authorization', is_relative=False)
        if client and secret and api_url:
            if config_obj.token:
                cek_tgl = datetime.now() + timedelta(seconds=10)
                if cek_tgl > fields.Datetime.from_string(config_obj.expired_on):
                    config_obj.generate_token_bca(api_url, client, secret)
            else:
                config_obj.generate_token_bca(api_url, client, secret)

            if not config_obj.token:
                return False
            token = f'Bearer {config_obj.token}'

            return token
        else:
            return False

    def generate_token_bca(self, url, client, secret):
        access_token = False
        credential = f'{client}:{secret}'.encode('utf-8')
        authorization = f"Basic {base64.b64encode(credential).decode('utf-8')}"
        payload = {'grant_type': 'client_credentials'}
        headers = {
            'Authorization': authorization,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(url=url, headers=headers, data=payload, verify=True)
        content = {}
        if response.status_code == 200:
            content = json.loads(response.content)
            access_token = content.get('access_token')
            self.suspend_security().write({
                'token': access_token,
                'expired_on': datetime.now() + timedelta(seconds=int(content.get('expires_in')))
            })
        
        # * Create Log
        name = 'Generate Token BCA'
        url = url
        request_type = 'post'
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        response_code = response.status_code
        params = {
            'name': name,
            'url': url,
            'description': name,
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

        return access_token
    
    def corporate_balance(self, accounts):
        config_obj = self._get_config_bank_by_name('BCA')
        corporate_url = self.env['tw.api.url'].sudo()._get_api_url_by_type(config_obj, 'corporates')
        list_account = accounts
        
        account_urllib = urllib.parse.quote(','.join(list_account))
        token = config_obj.get_token_bca(config_obj).split(' ')[1]
        body = config_obj.get_hash_body('')
        pst_now = config_obj.get_timestamp()

        content = f'GET:{corporate_url}/{config_obj.corporate_id}/accounts/{account_urllib}:{token}:{body}:{pst_now}'
        signature = self.utilities_signature(config_obj.api_secret, content)

        headers = {
            'X-BCA-Signature': signature,
            'X-BCA-Timestamp': pst_now,
            'Authorization': token,
            'X-BCA-Key': str(config_obj.api_key)
        }
        join_account = ','.join(list_account)
        
        ### Base URL/Corporate URL/Corporate ID/accounts/bank account ###
        url = f'{config_obj.base_url}{corporate_url}/{config_obj.corporate_id}/accounts/{join_account}'
        
        # Create Log
        name = 'Corporate Balance BCA'
        request_type = 'get'
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        content = {}
        payload = {}
        response_code = 400

        try:
            is_using_dummy = self.env['ir.config_parameter'].sudo().get_param('tw_b2b_bank_bca.dummy_balance_data')
            if is_using_dummy:
                content = eval(is_using_dummy)
                response_code = 200
                new_response = {'status_code': response_code, 'content': content}
                # Create a fake Response object
                response = requests.models.Response()
                response.status_code = new_response['status_code']
                response._content = json.dumps(new_response['content']).encode('utf-8')  # Must be bytes
            else:
                response = requests.get(url=url, headers=headers, verify=True)

            response_code = response.status_code
            content = response.content
            jml_data = 0
            content = json.loads(content)
            if response_code == 200:
                details = content.get('AccountDetailDataSuccess', [])
                jml_data = len(details)
            params = {
                'name': name,
                'url': url,
                'description': name,
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
            error = f'Exception {name} {err}'
            _logger.warning(error)
            params = {
                'name': name,
                'url': url,
                'description': error,
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

            return {'status': 0}
        
    def schedule_balance_bca(self):
        try:
            query = """
                SELECT
                    b.id
                    , MIN((sd.hour||':'||sd.minute)::TIME) AS schedule_time
                    , b.acc_number AS no_rekening
                FROM res_partner_bank b
                INNER JOIN tw_api_configuration ac ON ac.id = b.api_config_id
                INNER JOIN tw_selection ts ON ac.api_type_id = ts.id AND ts.type = 'ApiType'
                INNER JOIN tw_api_schedule s ON s.id = b.schedule_id
                INNER JOIN tw_api_schedule_line sd ON
                (
                    (b.last_balance_check + INTERVAL '7 hours')::DATE = CURRENT_DATE
                    AND (b.last_balance_check + INTERVAL '7 hours')::TIME < (sd.hour||':'||sd.minute)::TIME
                    AND (sd.hour||':'||sd.minute)::TIME < CURRENT_TIME
                )
                OR
                (
                    (b.last_balance_check + INTERVAL '7 hours')::DATE < CURRENT_DATE
                    AND (sd.hour||':'||sd.minute)::TIME < CURRENT_TIME
                )
                WHERE 1=1
                AND ts.name = 'BCA'
                GROUP BY b.id
                ORDER BY schedule_time ASC
                LIMIT 20 --Tidak boleh di ubah menjadi lebih besar karena ketentuan dari BCA adalah 20 rekening per hit.
            """
            self._cr.execute(query)
            ress = self._cr.dictfetchall()
            if ress:
                accounts = [res.get('no_rekening') for res in ress]
                corporate_account = self.corporate_balance(accounts)
                if corporate_account.get('status') == 1:
                    response = corporate_account.get('response')
                    if response.status_code == 200:
                        content = json.loads(response.content)
                        details = content.get('AccountDetailDataSuccess')
                        for detail in details:
                            bank_account = detail.get('AccountNumber')
                            dt_balance = detail.get('Balance')
                            partner_bank_obj = self.env['res.partner.bank'].sudo().search([('acc_number','=',bank_account)], limit=1)
                            if partner_bank_obj:
                                is_fetch_statement = False
                                last_balance = partner_bank_obj.balance
                                if abs(last_balance - float(dt_balance)) != 0:
                                    is_fetch_statement = True
                                elif partner_bank_obj.last_balance_check.date() < datetime.now().date():
                                    is_fetch_statement = True

                                vals = {
                                    'plafon': detail.get('Plafon'),
                                    'currency': detail.get('Currency'),
                                    'float_amount': detail.get('FloatAmount'),
                                    'hold_amount': detail.get('HoldAmount'),
                                    'available_balance': detail.get('AvailableBalance'),
                                    'balance': dt_balance,
                                    'is_fetch_statement': is_fetch_statement,
                                    'last_balance_check': datetime.now()
                                }
                                partner_bank_obj.sudo().write(vals)
                            else:
                                error = f'Balance BCA AccountNumber {bank_account} tidak ditemukan !'
                                _logger.warning(error)

        except Exception as err:
            error = f'Exception Balance BCA {err}'
            _logger.warning(error)

    def corporate_account_statements_bca(self, account, config_obj, corporate_url, last_fetch, end_date):
        token = config_obj.get_token_bca(config_obj).split(' ')[1]
        body = config_obj.get_hash_body('')
        pst_now = config_obj.get_timestamp()
        start_date = last_fetch
        
        content = f'GET:{corporate_url}/{config_obj.corporate_id}/accounts/{account}/statements?EndDate={end_date}&StartDate={start_date}:{token}:{body}:{pst_now}'
        signature = self.utilities_signature(config_obj.api_secret, content)
        
        headers = {
            'X-BCA-Signature': signature,
            'X-BCA-Timestamp': pst_now,
            'Authorization': token,
            'X-BCA-Key': str(config_obj.api_key)
        }

        ### Base URL/Corporate URL/Corporate ID/accounts/bank account/statements ###
        url = f'{config_obj.base_url}{corporate_url}/{config_obj.corporate_id}/accounts/{account}/statements'
        
        params = {
            'StartDate': start_date,
            'EndDate': end_date
        }

        # Create Log
        name = 'Corporate Statements BCA'
        request_type = 'get'
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        content = {}
        payload = {}
        response_code = 400

        try:
            is_using_dummy = self.env['ir.config_parameter'].sudo().get_param('tw_b2b_bank_bca.dummy_statements_data')
            if is_using_dummy:
                dummy_datas = eval(is_using_dummy)
                response_code = 200
                content = dummy_datas.get(account)
                if not content:
                    response_code = 401
                new_response = {'status_code': response_code, 'content': content}
                # Create a fake Response object
                response = requests.models.Response()
                response.status_code = new_response['status_code']
                response._content = json.dumps(new_response['content']).encode('utf-8')  # Must be bytes
            else:
                response = requests.get(url=url, headers=headers, params=params, verify=True)

            response_code = response.status_code
            content = response.content
            jml_data = 0
            content = json.loads(content)
            if response_code == 200:
                details = content.get('Data',[])
                jml_data = len(details)
            params = {
                'name': name,
                'url': url,
                'description': name,
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
            error = f'Exception {name} {err}'
            _logger.warning(error)
            params = {
                'name': name,
                'url': url,
                'description': error,
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

            return {'status': 0}
        
    def schedule_statements_bca(self):
        try:
            config_obj = self._get_config_bank_by_name('BCA')
            corporate_url = self.env['tw.api.url'].sudo()._get_api_url_by_type(config_obj, 'corporates')
            if config_obj and corporate_url:
                ress = self._get_statements_bca_data()
                if ress:
                    for res in ress:
                        master_id = res.get('id')
                        bank_account = res.get('acc_number')
                        account_id = res.get('account_id')
                        company_id = res.get('company_id')
                        last_fetch = res.get('last_fetch')
                        coa = res.get('coa')
                        end_date = res.get('end_date') #Current Date from Select Query
                        
                        master_bank_obj = self.env['res.partner.bank'].sudo().browse(master_id)
                        statement_account = self.corporate_account_statements_bca(bank_account, config_obj, corporate_url, last_fetch, end_date)
                        if statement_account.get('status') == 1:
                            response = statement_account.get('response')
                            if response.status_code == 200:
                                content = json.loads(response.content)
                                datas = content.get('Data')
                                
                                #### Delete All Transation PEND Bank Mutation ###
                                delete_bm = f"""
                                    DELETE FROM tw_bank_mutasi
                                    WHERE date IS NULL
                                    AND account_id = {account_id}
                                    AND company_id = {company_id}
                                    AND format = 'bca'
                                    AND state = 'Outstanding'
                                """
                                self._cr.execute(delete_bm)

                                for data in datas:
                                    transaction_name = data.get('TransactionName', '')
                                    trailer = data.get('Trailer', '')
                                    remark = str(transaction_name) + '  ' + str(trailer)
                                    transaction_type = data.get('TransactionType')
                                    transaction_amount = data.get('TransactionAmount')
                                    transaction_date = data.get('TransactionDate')
                                    tahun = date.today().year
                                    bln_now = date.today().month
                                    transaction_date_format = False
                                    if transaction_date != 'PEND':
                                        tgl, bln = transaction_date.split('/')
                                        if (int(bln) == 12) and (int(bln_now) == int(1)):
                                            tahun = tahun - 1
                                        transaction_date_format = str(tahun) + '-' + str(bln) + '-' + str(tgl)
                                        if end_date == transaction_date_format:
                                            # BCA mengupdate transaction date di H+1, 
                                            # hitungan H+1 di BCA lumayan berbeda karena jam 22:00 ke atas sudah di anggap pergantian hari 
                                            # Jika dibiarkan terbentuk, akan terbentuk double BM di H+1 nya.
                                            continue

                                    remark = remark.strip()
                                    vals = {
                                        'remark': remark,
                                        'coa': coa,
                                        'date': transaction_date_format,
                                        'account_id': account_id,
                                        'format': 'bca',
                                        'no_sistem': '',
                                        'company_id': company_id
                                    }
                                    debit = 0
                                    credit = 0
                                    if transaction_type == 'D':
                                        vals['debit'] = transaction_amount
                                        vals['credit'] = 0
                                    else:
                                        vals['credit'] = transaction_amount
                                        vals['debit'] = 0
                                    
                                    # * Bank IN Auto Posted
                                    if (remark[0:17] == 'TRSF E-BANKING DB') and (remark[-23:] == 'KE PS TUNAS DWIPA MATRA') and coa[0:6] == '111205':
                                        vals['is_posted'] = True
                                    
                                    params_transaction = ['PAJAK BUNGA', 'BIAYA ADM', 'BUNGA']
                                    if str(transaction_name) in params_transaction:
                                        cek_bm = self.env['tw.bank.mutasi'].sudo().search([
                                            ('company_id','=',company_id),
                                            ('date','=',transaction_date_format),
                                            ('remark','=',remark),
                                            ('account_id','=',account_id),
                                            ('amount','=',transaction_amount),
                                            ('format','=','bca')
                                        ], limit=1)
                                        if not cek_bm:
                                            # * Bank IN Auto Posted
                                            if coa[0:6] == '111205':
                                                vals['is_posted'] = True
                                            create_bm = self.env['tw.bank.mutasi'].sudo().create(vals)
                                    else:
                                        if str(transaction_name) in ['CR KOREKSI BUNGA', 'DR KOREKSI BUNGA']:
                                            cek_bm = self.env['tw.bank.mutasi'].sudo().search([
                                                ('company_id','=',company_id),
                                                ('date','=',transaction_date_format),
                                                ('remark','=',remark),
                                                ('account_id','=',account_id),
                                                ('amount','=',transaction_amount),
                                                ('format','=','bca')
                                            ], limit=1)
                                            if cek_bm:
                                                continue
                                        create_bm = self.env['tw.bank.mutasi'].sudo().create(vals)
                                
                                ### Update Bank Status Fetch Statement ###
                                master_bank_obj.sudo().write({
                                    'is_fetch_statement': False,
                                    'last_fetch': datetime.now()
                                })
                                
                            elif response.status_code == 404:
                                ### Update Bank Status Fetch Statement ###
                                master_bank_obj.sudo().write({
                                    'is_fetch_statement': False,
                                    'last_fetch': datetime.now()
                                })

        except Exception as err:
            error = f'Exception Statements BCA {err}'
            _logger.warning(error)

    # 14: private methods
    def _get_statements_bca_data(self):
        query = """
            SELECT
                b.id
                , b.acc_number
                , b.account_id
                , b.company_id
                , aa.code_store ->> '1' AS coa
                , ((b.last_fetch + INTERVAL '7 hours')::DATE)::TEXT AS last_fetch
                , (CURRENT_DATE)::TEXT AS end_date
            FROM res_partner_bank b
            INNER JOIN tw_api_configuration ac ON ac.id = b.api_config_id
            INNER JOIN tw_selection ts ON ac.api_type_id = ts.id AND ts.type = 'ApiType'
            INNER JOIN account_account aa ON aa.id = b.account_id
            WHERE 1=1
            AND b.is_fetch_statement = TRUE
            AND ts.name = 'BCA'
            ORDER BY b.last_balance_check ASC
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        
        return ress