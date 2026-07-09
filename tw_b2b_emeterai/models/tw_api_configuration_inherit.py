# 1: imports of python lib
from datetime import datetime, timedelta
import requests
import json
import base64

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.api import Environment

# 5: local imports

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
    def action_open_config_parameter_url_emeterai(self):
        self.ensure_one()
        list_view_id = self.env.ref('base.view_ir_config_list').id
        form_view_id = self.env.ref('base.view_ir_config_form').id
        search_view_id = self.env.ref('base.view_ir_config_search').id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.config_parameter',
            'view_type': 'form',
            'view_mode': 'list,form',
            'domain': [('key','like','peruri')],
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id
        }
    
    def action_generate_token_peruri(self, is_regenerate=False):
        method = 'POST'
        url = f'{self.base_url}/api/users/login'
        headers = self._get_headers_peruri()

        try:
            log_name = 'B2B Peruri New Login (Generate Token)'
            request_type = method.lower()
            description = log_name
            ip_address = ''
            method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
            model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)

            body_data = {
                'user': self.username,
                'password': self.password
            }
            response = requests.request(method, url, headers=headers, json=body_data)

            # Process Response
            if response.status_code == 200:
                now = datetime.now()
                content = json.loads(response.content)
                status_code = content.get('statusCode')
                if status_code == '00':
                    token = content.get('token')
                    result = content.get('result')
                    data = result.get('data')
                    login = data.get('login')
                    user = login.get('user')
                    id = user.get('id')
                    if not self.token:
                        bearer_token = self.suspend_security().write({
                            'token': token,
                            'expired_on': now + timedelta(minutes=15)
                        })
                    else:
                        if is_regenerate:
                            bearer_token = self.suspend_security().write({
                                'token': token,
                                'expired_on': now + timedelta(minutes=15)
                            })

                    return token
                else:
                    with self.pool.cursor() as new_cr:
                        new_env = Environment(new_cr, self.env.uid, dict(self.env.context))

                        # * create api log
                        description = 'Failed Generate Token Peruri !'
                        new_env['tw.api.log'].sudo().create_api_log(
                            log_name,
                            url,
                            description,
                            ip_address,
                            content,
                            body_data,
                            headers,
                            response_code=response.status_code,
                            status_code=response.status_code,
                            reference='',
                            transaction_id=None,
                            api_type_id=self.api_type_id.id,
                            method_id=method_obj.id if method_obj else False,
                            model_id=model_obj.id if model_obj else False
                        )
                        new_cr.commit()

                    raise Warning(description)
            else:
                try:
                    content = json.loads(response.content)
                    status_code = content.get('statusCode')
                    msg = content.get('message', False) or str(content)
                    if status_code and status_code != '00':
                        result = content.get('result')
                        msg = result
                except Exception as err:
                    msg = str(response.content)
                
                with self.pool.cursor() as new_cr:
                    new_env = Environment(new_cr, self.env.uid, dict(self.env.context))

                    description = f'Failed generate token Peruri with error: {msg}'
                    new_env['tw.api.log'].sudo().create_api_log(
                        log_name,
                        url,
                        description,
                        ip_address,
                        content,
                        body_data,
                        headers,
                        response_code=response.status_code,
                        status_code=response.status_code,
                        reference='',
                        transaction_id=None,
                        api_type_id=self.api_type_id.id,
                        method_id=method_obj.id if method_obj else False,
                        model_id=model_obj.id if model_obj else False
                    )
                    new_cr.commit()

                raise Warning(description)
        except Exception as err:
            raise Warning(f'There is an error when sending API : \n{str(err)}')
        
    def action_check_limit_quota_stamp_peruri(self):
        if not self.token:
            token = self.action_generate_token_peruri()
        else:
            token = self._get_token_peruri()

        method = 'POST'
        url = f'{self.base_url}/function/saldopos'
        headers = self._get_headers_peruri()

        try:
            log_name = 'B2B Peruri Check Limit Quota Stamp'
            request_type = method.lower()
            description = log_name
            ip_address = ''
            method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
            model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
            
            headers.update({
                'Authorization': f'Bearer {token}',
                'csrf-token': token
            })
            response = requests.request(method, url, headers=headers)

            # Process Response
            if response.status_code == 200:
                content = json.loads(response.content)
                # status_code = content.get('statusCode')
                # status_code = response.status_code
                result = content.get('result')
                status_code = content.get('status')
                if status_code and status_code != '00':
                    msg = content.get('message', False) or str(content)
                    if result:
                        msg = result
                    
                    with self.pool.cursor() as new_cr:
                        new_env = Environment(new_cr, self.env.uid, dict(self.env.context))
                        
                        # * create api log
                        description = msg
                        new_env['tw.api.log'].sudo().create_api_log(
                            log_name,
                            url,
                            description,
                            ip_address,
                            content,
                            {},
                            headers,
                            response_code=response.status_code,
                            status_code=response.status_code,
                            reference='',
                            transaction_id=None,
                            api_type_id=self.api_type_id.id,
                            method_id=method_obj.id if method_obj else False,
                            model_id=model_obj.id if model_obj else False
                        )
                        new_cr.commit()

                    raise Warning(description)
                else:
                    saldo = result.get('saldo')
                    notstamp = result.get('notstamp')
                    is_warning = False
                    if saldo < 1:
                        is_warning = True

                        with self.pool.cursor() as new_cr:
                            new_env = Environment(new_cr, self.env.uid, dict(self.env.context))
                            
                            # * create api log
                            description = f'Balance sisa E-Meterai tidak cukup, saat ini bersisa: {str(saldo)}'
                            new_env['tw.api.log'].sudo().create_api_log(
                                log_name,
                                url,
                                description,
                                ip_address,
                                content,
                                {},
                                headers,
                                response_code=response.status_code,
                                status_code=response.status_code,
                                reference='',
                                transaction_id=None,
                                api_type_id=self.api_type_id.id,
                                method_id=method_obj.id if method_obj else False,
                                model_id=model_obj.id if model_obj else False
                            )
                            new_cr.commit()
                    
                    key = 'peruri.saldo'
                    with self.pool.cursor() as new_cr:
                        new_env = Environment(new_cr, self.env.uid, dict(self.env.context))

                        config_parameter_model = new_env['ir.config_parameter'].sudo()
                        config_param_saldo_peruri_obj = config_parameter_model.search([('key','=',key)], limit=1)
                        if config_param_saldo_peruri_obj:
                            if int(config_param_saldo_peruri_obj.value) != saldo:
                                config_param_saldo_peruri_obj.sudo().write({'value': str(saldo)})
                        else:
                            config_param_saldo_peruri_obj = config_parameter_model.sudo().create({
                                'key': key,
                                'value': str(saldo)
                            })
                        new_cr.commit()

                    if is_warning:
                        raise Warning(description)
                    
                    return config_param_saldo_peruri_obj
            else:
                try:
                    content = json.loads(response.content)
                    status_code = content.get('statusCode')
                    msg = content.get('message', False) or str(content)
                    if status_code and status_code != '00':
                        result = content.get('result')
                        msg = result
                except Exception as err:
                    msg = str(response.content)
                
                with self.pool.cursor() as new_cr:
                    new_env = Environment(new_cr, self.env.uid, dict(self.env.context))

                    # * create api log
                    description = f'Failed check limit quota Peruri with error: {msg}'
                    new_env['tw.api.log'].sudo().create_api_log(
                        log_name,
                        url,
                        description,
                        ip_address,
                        content,
                        {},
                        headers,
                        response_code=response.status_code,
                        status_code=response.status_code,
                        reference='',
                        transaction_id=None,
                        api_type_id=self.api_type_id.id,
                        method_id=method_obj.id if method_obj else False,
                        model_id=model_obj.id if model_obj else False
                    )
                    new_cr.commit()

                raise Warning(description)
        except Exception as err:
            raise Warning(f'There is an error when sending API : \n{str(err)}')
        
    def action_upload_doc_peruri(self, datas={}):
        method = 'POST'
        base_url_upload_doc_peruri = self.env['ir.config_parameter'].sudo().get_param('peruri.upload.doc.url')
        if not base_url_upload_doc_peruri:
            raise Warning('Base URL Upload Doc Peruri tidak ada !')
        
        url = f'{base_url_upload_doc_peruri}/uploaddoc2'
        error = ''
        try:
            check_limit_quota_stamp = self.action_check_limit_quota_stamp_peruri()
        except Exception as err:
            check_limit_quota_stamp = False
            error = err
        
        if check_limit_quota_stamp:
            if not self.token:
                token = self.action_generate_token_peruri()
            else:
                token = self._get_token_peruri()
            headers = self._get_headers_peruri()

            try:
                log_name = 'B2B Peruri Upload Doc File'
                request_type = method.lower()
                description = log_name
                ip_address = ''
                method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
                model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
                
                base64_file = datas.get('pdf')
                file_data = base64.b64decode(base64_file)
                filename = datas.get('filename')
                files = {
                    'file': (filename, file_data, 'application/octet-stream')
                }
                headers = {'Authorization': f'Bearer {token}'}
                body_data = {'token': token}
                response = requests.request(method, url, headers=headers, files=files, data=body_data)

                # Process Response
                if response.status_code == 200:
                    content = json.loads(response.content)
                    status_code = content.get('statusCode')
                    message = content.get('message')
                    result = content.get('result')
                    if status_code == '00':
                        idfile = content.get('id')
                        namafile = content.get('name')
                        filestamp = f'/sharefolder/final_{idfile}.pdf'
                        file = f'/sharefolder/doc_{idfile}.pdf'
                        upload_doc_peruri = {
                            'idfile': idfile,
                            'namafile': namafile,
                            'filestamp': filestamp,
                            'file': file
                        }
                        datas['upload_doc_peruri'] = upload_doc_peruri
                        
                        return datas
                    else:
                        with self.pool.cursor() as new_cr:
                            new_env = Environment(new_cr, self.env.uid, dict(self.env.context))
                            
                            # * create api log
                            description = f'Failed upload doc file !\n\nError:\nMessage: {message}\nResult: {result}'
                            new_env['tw.api.log'].sudo().create_api_log(
                                log_name,
                                url,
                                description,
                                ip_address,
                                content,
                                body_data,
                                headers,
                                response_code=response.status_code,
                                status_code=response.status_code,
                                reference='',
                                transaction_id=None,
                                api_type_id=self.api_type_id.id,
                                method_id=method_obj.id if method_obj else False,
                                model_id=model_obj.id if model_obj else False
                            )
                            new_cr.commit()

                        raise Warning(description)
                else:
                    try:
                        content = json.loads(response.content)
                        status_code = content.get('statusCode')
                        msg = content.get('message', False) or str(content)
                    except Exception as err:
                        msg = str(response.content)
                    
                    with self.pool.cursor() as new_cr:
                        new_env = Environment(new_cr, self.env.uid, dict(self.env.context))
                        
                        # * create api log
                        description = f'Failed upload doc file Peruri with error: {msg}'
                        new_env['tw.api.log'].sudo().create_api_log(
                            log_name,
                            url,
                            description,
                            ip_address,
                            content,
                            body_data,
                            headers,
                            response_code=response.status_code,
                            status_code=response.status_code,
                            reference='',
                            transaction_id=None,
                            api_type_id=self.api_type_id.id,
                            method_id=method_obj.id if method_obj else False,
                            model_id=model_obj.id if model_obj else False
                        )
                        new_cr.commit()

                    raise Warning(description)
            except Exception as err:
                raise Warning(f'There is an error when sending API : \n{str(err)}')
        else:
            raise Warning(f'Failed to Check Limit Quota Stamp e-Meterai !\nError: {error}')
        
    def action_generate_sn_peruri(self, datas={}):
        method = 'POST'
        base_url_generate_sn_peruri = self.env['ir.config_parameter'].sudo().get_param('peruri.generate.sn.url')
        if not base_url_generate_sn_peruri:
            raise Warning('Base URL Generate SN Peruri tidak ada !')
        
        url = f'{base_url_generate_sn_peruri}/chanel/stampv2'
        if datas:
            if not self.token:
                token = self.action_generate_token_peruri()
            else:
                token = self._get_token_peruri()
            headers = self._get_headers_peruri()

            try:
                log_name = 'B2B Peruri Generate SN'
                request_type = method.lower()
                description = log_name
                ip_address = ''
                method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
                model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
                
                nama_doc = self.env['ir.config_parameter'].sudo().get_param('peruri.nama.doc') or '2'
                upload_doc_peruri = datas.get('upload_doc_peruri')
                headers.update({'Authorization': f'Bearer {token}'})
                body_data = {
                    'idfile': upload_doc_peruri.get('idfile'),
                    'isUpload': True,
                    'namadoc': nama_doc,
                    'namafile': upload_doc_peruri.get('namafile'),
                    'nilaidoc': False,
                    'snOnly': False,
                    'nodoc': '0',
                    'tgldoc': False
                }
                response = requests.request(method, url, headers=headers, json=body_data)
                
                # Process Response
                if response.status_code == 200:
                    content = json.loads(response.content)
                    status_code = content.get('statusCode')
                    if status_code == '00':
                        result = content.get('result')
                        sn = result.get('sn')
                        filename_qr = result.get('filenameQR')
                        file_qr = f'/sharefolder/{filename_qr}'
                        generate_sn_peruri = {
                            'serialNumber': sn,
                            'fileQr': file_qr
                        }
                        datas['generate_sn_peruri'] = generate_sn_peruri
                        
                        return datas
                    else:
                        with self.pool.cursor() as new_cr:
                            new_env = Environment(new_cr, self.env.uid, dict(self.env.context))
                            
                            # * create api log
                            description = 'Failed generate SN !'
                            new_env['tw.api.log'].sudo().create_api_log(
                                log_name,
                                url,
                                description,
                                ip_address,
                                content,
                                body_data,
                                headers,
                                response_code=response.status_code,
                                status_code=response.status_code,
                                reference='',
                                transaction_id=None,
                                api_type_id=self.api_type_id.id,
                                method_id=method_obj.id if method_obj else False,
                                model_id=model_obj.id if model_obj else False
                            )
                            new_cr.commit()
                        
                        raise Warning(description)
                else:
                    try:
                        content = json.loads(response.content)
                        status_code = content.get('statusCode')
                        msg = content.get('message', False) or str(content)
                    except Exception as err:
                        msg = str(response.content)
                    
                    with self.pool.cursor() as new_cr:
                        new_env = Environment(new_cr, self.env.uid, dict(self.env.context))

                        # * create api log
                        description = f'Failed generate SN Peruri with error: {msg}'
                        new_env['tw.api.log'].sudo().create_api_log(
                            log_name,
                            url,
                            description,
                            ip_address,
                            content,
                            body_data,
                            headers,
                            response_code=response.status_code,
                            status_code=response.status_code,
                            reference='',
                            transaction_id=None,
                            api_type_id=self.api_type_id.id,
                            method_id=method_obj.id if method_obj else False,
                            model_id=model_obj.id if model_obj else False
                        )
                        new_cr.commit()

                    raise Warning(description)
            except Exception as err:
                raise Warning(f'There is an error when sending API : \n{str(err)}')
        else:
            return False
        
    def action_check_status_sn_peruri(self, filter_sn=None):
        method = 'GET'
        url = f'{self.base_url}/api/chanel/stamp/ext'
        if filter_sn:
            if not self.token:
                token = self.action_generate_token_peruri()
            else:
                token = self._get_token_peruri()
            headers = self._get_headers_peruri()

            try:
                log_name = 'B2B Peruri Check Status SN'
                request_type = method.lower()
                description = log_name
                ip_address = ''
                method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
                model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)

                headers.update({'Authorization': f'Bearer {token}'})
                if filter_sn:
                    url += f'?filter={filter_sn}'
                response = requests.request(method, url, headers=headers)

                # Process Response
                if response.status_code == 200:
                    content = json.loads(response.content)
                    status_code = content.get('statusCode')
                    if status_code == '00':
                        result = content.get('result')
                        total = result.get('total')
                        status = False
                        if total > 0:
                            data = result.get('data')[0]
                            status = data.get('status')
                        
                        return status
                    else:
                        with self.pool.cursor() as new_cr:
                            new_env = Environment(new_cr, self.env.uid, dict(self.env.context))
                            
                            # * create api log
                            description = 'Failed check status SN !'
                            new_env['tw.api.log'].sudo().create_api_log(
                                log_name,
                                url,
                                description,
                                ip_address,
                                content,
                                {},
                                headers,
                                response_code=response.status_code,
                                status_code=response.status_code,
                                reference='',
                                transaction_id=None,
                                api_type_id=self.api_type_id.id,
                                method_id=method_obj.id if method_obj else False,
                                model_id=model_obj.id if model_obj else False
                            )
                            new_cr.commit()

                        raise Warning(description)
                else:
                    try:
                        content = json.loads(response.content)
                        status_code = content.get('statusCode')
                        msg = content.get('message', False) or str(content)
                    except Exception as err:
                        msg = str(response.content)
                    
                    with self.pool.cursor() as new_cr:
                        new_env = Environment(new_cr, self.env.uid, dict(self.env.context))
                        
                        # * create api log
                        description = f'Failed check status SN Peruri with error: {msg}'
                        new_env['tw.api.log'].sudo().create_api_log(
                            log_name,
                            url,
                            description,
                            ip_address,
                            content,
                            {},
                            headers,
                            response_code=response.status_code,
                            status_code=response.status_code,
                            reference='',
                            transaction_id=None,
                            api_type_id=self.api_type_id.id,
                            method_id=method_obj.id if method_obj else False,
                            model_id=model_obj.id if model_obj else False
                        )
                        new_cr.commit()

                    raise Warning(description)
            except Exception as err:
                raise Warning(f'There is an error when sending API : \n{str(err)}')
        else:
            return False
        
    def action_stamp_peruri(self, datas={}, re_stamping=False):
        method = 'POST'
        base_url_stamp_peruri = self.env['ir.config_parameter'].sudo().get_param('peruri.stamp.url')
        if not base_url_stamp_peruri:
            raise Warning('Base URL Stamp Peruri tidak ada !')
        
        url = f'{base_url_stamp_peruri}/keystamp/adapter/docSigningZ'
        if datas:
            if not self.token:
                token = self.action_generate_token_peruri()
            else:
                token = self._get_token_peruri()
            headers = self._get_headers_peruri()

            try:
                log_name = 'B2B Peruri Stamping'
                request_type = method.lower()
                description = log_name
                ip_address = ''
                method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
                model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)

                upload_doc_peruri = datas.get('upload_doc_peruri')
                generate_sn_peruri = datas.get('generate_sn_peruri')
                headers.update({'Authorization': f'Bearer {token}'})
                body_data = {
                    'onPrem': False,
                    'docId': upload_doc_peruri.get('idfile'),
                    'certificatelevel': 'NOT_CERTIFIED',
                    'dest': upload_doc_peruri.get('filestamp'),
                    'docpass': '',
                    'jwToken': token,
                    'location': 'LAMPUNG',
                    'profileName': 'emeteraicertificateSigner',
                    'reason': 'Hutang Lain',
                    'refToken': generate_sn_peruri.get('serialNumber'),
                    'spesimenPath': generate_sn_peruri.get('fileQr'),
                    'src': upload_doc_peruri.get('file'),
                    'visLLX': datas.get('visLLX'),
                    'visLLY': datas.get('visLLY'),
                    'visURX': datas.get('visURX'),
                    'visURY': datas.get('visURY'),
                    'visSignaturePage': datas.get('page')
                }
                if re_stamping:
                    body_data['retryFlag'] = '1'
                response = requests.request(method, url, headers=headers, json=body_data)

                # Process Response
                if response.status_code == 200:
                    content = json.loads(response.content)
                    status = content.get('status')
                    status_code = content.get('errorCode')
                    if status == 'True' and status_code == '00':
                        srcfileStamp = content.get('urlFile')
                        datas['srcfileStamp'] = srcfileStamp
                        
                        return datas
                    else:
                        with self.pool.cursor() as new_cr:
                            new_env = Environment(new_cr, self.env.uid, dict(self.env.context))
                            
                            # * create api log
                            description = 'Failed stamping !'
                            new_env['tw.api.log'].sudo().create_api_log(
                                log_name,
                                url,
                                description,
                                ip_address,
                                content,
                                body_data,
                                headers,
                                response_code=response.status_code,
                                status_code=response.status_code,
                                reference='',
                                transaction_id=None,
                                api_type_id=self.api_type_id.id,
                                method_id=method_obj.id if method_obj else False,
                                model_id=model_obj.id if model_obj else False
                            )
                            new_cr.commit()

                        raise Warning(description)
                else:
                    try:
                        content = json.loads(response.content)
                        status_code = content.get('statusCode')
                        msg = content.get('message', False) or str(content)
                    except Exception as err:
                        msg = str(response.content)
                    
                    with self.pool.cursor() as new_cr:
                        new_env = Environment(new_cr, self.env.uid, dict(self.env.context))
                        
                        # * create api log
                        description = f'Failed stamping Peruri with error: {msg}'
                        new_env['tw.api.log'].sudo().create_api_log(
                            log_name,
                            url,
                            description,
                            ip_address,
                            content,
                            body_data,
                            headers,
                            response_code=response.status_code,
                            status_code=response.status_code,
                            reference='',
                            transaction_id=None,
                            api_type_id=self.api_type_id.id,
                            method_id=method_obj.id if method_obj else False,
                            model_id=model_obj.id if model_obj else False
                        )
                        new_cr.commit()

                    raise Warning(description)
            except Exception as err:
                raise Warning(f'There is an error when sending API : \n{str(err)}')
        else:
            return False
        
    def action_download_file_stamp_peruri(self, datas={}, doc_id=None):
        method = 'GET'
        url = False
        if datas.get('srcfileStamp'):
            url = datas.get('srcfileStamp')
        else:
            if doc_id:
                base_url_upload_doc_peruri = self.env['ir.config_parameter'].sudo().get_param('peruri.upload.doc.url')
                if not base_url_upload_doc_peruri:
                    raise Warning('Base URL Upload Doc Peruri tidak ada !')
                url = f'{base_url_upload_doc_peruri}/getfile3/final_{doc_id}.pdf'

        if not url:
            raise Warning('URL Download File Stamp Peruri tidak ada !')
        if not self.token:
            token = self.action_generate_token_peruri()
        else:
            token = self._get_token_peruri()
        headers = self._get_headers_peruri()

        try:
            log_name = 'B2B Peruri Download File Stamping'
            request_type = method.lower()
            description = log_name
            ip_address = ''
            method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
            model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)

            headers.update({
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/pdf'
            })
            response = requests.request(method, url, headers=headers)
            
            # Process Response
            if response.status_code == 200:
                content = response.content
                file_stamped = base64.b64encode(content)
                
                return file_stamped
            else:
                try:
                    content = json.loads(response.content)
                    status_code = content.get('statusCode')
                    msg = content.get('message', False) or str(content)
                except Exception as err:
                    msg = str(response.content)
                
                with self.pool.cursor() as new_cr:
                    new_env = Environment(new_cr, self.env.uid, dict(self.env.context))
                    
                    # * create api log
                    description = f'Failed download stamping file Peruri with error: {msg}'
                    new_env['tw.api.log'].sudo().create_api_log(
                        log_name,
                        url,
                        description,
                        ip_address,
                        content,
                        {},
                        headers,
                        response_code=response.status_code,
                        status_code=response.status_code,
                        reference='',
                        transaction_id=None,
                        api_type_id=self.api_type_id.id,
                        method_id=method_obj.id if method_obj else False,
                        model_id=model_obj.id if model_obj else False
                    )
                    new_cr.commit()

                raise Warning(description)
        except Exception as err:
            raise Warning(f'There is an error when sending API : \n{str(err)}')

    # 14: private methods
    def _get_headers_peruri(self):
        return {'Content-Type': 'application/json'}
    
    def _check_expired_token_peruri(self, now, expired_on_token):
        # token_expired_on = datetime.strptime(expired_on_token, '%Y-%m-%d %H:%M:%S')
        token_expired_on = expired_on_token
        if token_expired_on < now:
            return True
        return False
    
    def _get_token_peruri(self):
        now = datetime.now()
        token = self.token
        is_expired_token = self._check_expired_token_peruri(now, self.expired_on)
        if is_expired_token:
            token = self.action_generate_token_peruri(is_regenerate=True)
        return token