# 1: imports of python lib
from datetime import datetime, timedelta
import requests
import json
import pytz
import hmac
import hashlib
import base64

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
    def get_time_bri(self):
        pst_now = pytz.UTC.localize(fields.Datetime.now()).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))
        pst_now = pst_now - timedelta(hours=7)
        pst_now = pst_now.isoformat(timespec='microseconds')
        pst_now = pst_now[:-9] + 'Z'
        
        return pst_now
    
    def action_get_token_bri_manual(self):
        api_type_obj = self.api_type_id
        if api_type_obj.name == 'BRI QRIS':
            # self._generate_qris_token()
            return True
        elif api_type_obj.name == 'BRI':
            api_url = self.env['tw.api.url'].sudo()._get_api_url_by_type(self, 'authorization')
            url = f'{self.base_url}{api_url}'
            
            return self.generate_token_bri(url, self.api_key, self.api_secret)

    def get_token_bri(self, config_obj):
        client = config_obj.api_key
        secret = config_obj.api_secret
        api_url = self.env['tw.api.url'].sudo()._get_api_url_by_type(self, 'authorization')
        if client and secret and api_url:
            if config_obj.token:
                cek_tgl = datetime.now() + timedelta(seconds=10)
                if cek_tgl > fields.Datetime.from_string(config_obj.expired_on):
                    config_obj.generate_token_bri(api_url, client, secret)
            else:
                config_obj.generate_token_bri(api_url, client, secret)
            
            if not config_obj.token:
                return False
            token = f'Bearer {config_obj.token}'

            return token
        else:
            return False

    def generate_token_bri(self, url, client, secret):
        access_token = False
        payload = f'client_id={client}&client_secret={secret}'
        headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
        }
        response = requests.post(url=url, headers=headers, data=payload)
        content = {}
        if response.status_code == 200:
            content = json.loads(response.content)
            access_token = content.get('access_token')
            self.suspend_security().write({
                'token': access_token,
                'expired_on': datetime.now() + timedelta(seconds=int(content.get('expires_in')))
            })
        
        # * Create Log
        name = 'Generate Token BRI'
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
    
    def corporate_account_statements_bri(self, config_obj, account, base_url, start_date, end_date):
        client = config_obj.api_key
        secret = config_obj.api_secret
        path = f'/v1/statement/{account}/{start_date}/{end_date}'
        url = f'{base_url}{path}'
        verb = 'GET'
        token = self.get_token_bri(config_obj)
        timestamp = self.get_time_bri()
        body = ''
        result = f'path={path}&verb={verb}&token={token}&timestamp={timestamp}&body={body}'
        
        # * encode secret and result to bytes
        secret_bytes = str(secret).encode('utf-8')
        result_bytes = str(result).encode('utf-8')
        h = hmac.new(secret_bytes, result_bytes, hashlib.sha256)
        signature = base64.b64encode(h.digest()).decode('utf-8')

        payload = {}
        headers = {
          'BRI-Signature': signature,
          'BRI-Timestamp': timestamp,
          'Authorization': token
        }
        # * create log
        name = 'Corporate Statements BRI'
        request_type = 'get'
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        content = {}
        response_code = 400

        try:
            response = requests.get(url=url, headers=headers, data=payload)
            response_code = response.status_code
            content = response.content
            jml_data = 0
            if response_code == 200:
                content = json.loads(response.content)
                datas = content.get('data')
                jml_data = len(datas)
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
            error = f'Corporate Statements BRI {err}'
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
        
    def schedule_statements_bri(self):
        try:
            ress = self._get_statements_bri_data()
            for res in ress:
                master_id = res.get('id')
                no_rekening = res.get('no_rekening')
                base_url = res.get('base_url')
                account_id = res.get('account_id')
                company_id = res.get('company_id')
                start_date = res.get('last_fetch')
                coa = res.get('coa')
                end_date = res.get('end_date')
                h_min_1 = res.get('h_min_1')
                config_id = self.browse(res.get('config_id'))
                statement_account = self.corporate_account_statements_bri(config_id, no_rekening, base_url, start_date, end_date)

                if statement_account.get('status') == 1:
                    response = statement_account.get('response')
                    if response.status_code == 200:
                        content = json.loads(response.content)
                        datas = content.get('data')

                        #### Delete All Transation PEND Bank Mutation ###
                        delete_bm = f"""
                            DELETE FROM tw_bank_mutasi
                            WHERE date IS NULL
                            AND account_id = {account_id}
                            AND company_id = {company_id}
                            AND format = 'bri'
                            AND state = 'Outstanding'
                        """
                        self._cr.execute(delete_bm)

                        for data in datas:
                            # Data Responses #
                            mutasi_debet = data.get('mutasi_debet')
                            ket_tran = data.get('ket_tran') 
                            saldo_akhir_mutasi = data.get('saldo_akhir_mutasi')
                            channel_id = data.get('channel_id') 
                            tanggal_tran = data.get('tanggal_tran') 
                            saldo_awal_mutasi = data.get('saldo_awal_mutasi')
                            kode_tran = data.get('kode_tran') 
                            mutasi_kredit = data.get('mutasi_kredit')
                            nomor_rekening = data.get('nomor_rekening') 
                            nomor_reff = data.get('nomor_reff')
                            posisi_neraca = data.get('posisi_neraca')
                            
                            tgl_rk = False
                            if tanggal_tran:
                                tgl_rk = tanggal_tran[0:10]

                            vals = {
                                'remark': ket_tran,
                                'coa': coa,
                                'account_id': account_id,
                                'format': 'bri',
                                'no_sistem': '',
                                'company_id': company_id
                            }
                            if posisi_neraca == 'Debit':
                                vals['debit'] = mutasi_debet
                            elif posisi_neraca == 'Kredit':
                                vals['credit'] = mutasi_kredit

                            # * Cek h-1 Transaksi Update Date BM
                            if (tgl_rk == start_date) and (tgl_rk == h_min_1):
                                vals['date'] = tgl_rk
                                create_bm = self.env['tw.bank.mutasi'].sudo().create(vals)
                            # * Cek tgl hari ini pending
                            elif tgl_rk == end_date:
                                create_bm = self.env['tw.bank.mutasi'].sudo().create(vals)

                        ### Update Bank Status Fetch Statement ###
                        update_master_bank = f"""
                            UPDATE res_partner_bank
                            SET last_fetch = '{datetime.now().isoformat()}', balance = '{saldo_akhir_mutasi}'
                            WHERE id = {master_id}
                        """
                        self._cr.execute(update_master_bank) 
                    elif response.status_code == 400:
                        content = json.loads(response.content)
                        status = content.get('code')
                        #95 : no transaction found in BRI, 99 : General Error
                        # if str(status) in ('95','99'): 
                        if str(status) in ('95'): 
                            ### Update Bank Status Fetch Statement ###
                            update_master_bank = f"""
                                UPDATE res_partner_bank
                                SET last_fetch = '{datetime.now().isoformat()}'
                                WHERE id = {master_id}
                            """
                            self._cr.execute(update_master_bank) 

        except Exception as err:
            error = f'Exception Statements BRI {err}'
            _logger.warning(error)

    # 14: private methods
    def _get_statements_bri_data(self):
        query = """
            SELECT
                b.id
                , MIN((sd.hour||':'||sd.minute)::TIME) AS schedule_time
                , b.acc_number AS no_rekening
                , (COALESCE((b.last_fetch + INTERVAL '7 hours')::DATE, NOW()::DATE))::TEXT AS last_fetch
                , b.account_id
                , b.company_id
                , ac.base_url
                , ac.id AS config_id
                , aa.code_store ->> '1' AS coa
                , (CURRENT_DATE)::TEXT AS end_date
                , (CURRENT_DATE - 1)::TEXT AS h_min_1
            FROM res_partner_bank b
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
            AND ts.name = 'BRI'
            GROUP BY b.id, ac.id, aa.id
            ORDER BY schedule_time ASC
            LIMIT 25
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        
        return ress