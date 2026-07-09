from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning
import json
import requests

class InheritB2BApiConfig(models.Model):
    _inherit = "tw.api.configuration"

    open_id = fields.Char(string='Open ID URL')
    audience = fields.Char(string='Audience')
    issuer = fields.Char(string='Issuer')

    def action_open_config_parameter_url_koprol(self):
        self.ensure_one()
        list_view_id = self.env.ref('base.view_ir_config_list').id
        form_view_id = self.env.ref('base.view_ir_config_form').id
        search_view_id = self.env.ref('base.view_ir_config_search').id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.config_parameter',
            'view_type': 'form',
            'view_mode': 'list,form',
            'domain': [('key','like','koprol')],
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id
        }

    def _get_koprol_endpoint(self, code):
        """Get endpoint configuration by code from tw.endpoint.configuration"""
        self.ensure_one()
        endpoint = self.endpoint_config_ids.filtered(
            lambda e: e.code == code and e.active
        )
        if not endpoint:
            raise Warning(f'Endpoint dengan code "{code}" belum dikonfigurasi untuk API {self.name}!')
        return endpoint[0]

    def generate_token_azure(self):
        """Generate/refresh Azure token and return it"""
        # Check if token refresh is needed
        need_refresh = False
        if not self.token:
            need_refresh = True
        elif self.expired_on:
            if datetime.now() > self.expired_on:
                need_refresh = True
        else:
            need_refresh = True
        
        if need_refresh:
            self.get_azure_access_token()
        
        return self.token
    
    def check_status_koprol(self, data):
        endpoint = self._get_koprol_endpoint('koprol.update.status.po')
        url = endpoint.full_url
        token = self.generate_token_azure()
        headers = {
            "authorization": "Bearer %s" % token,
            "content-type": "application/json",
        }    
        verify = self.verify
        try:
            log_name = "B2B Koprol Check Status"
            log_type = "outgoing"
            log_request_type = "post"
            log_request = {'headers': headers, 'body': data}
            response = requests.post(url=url, json=data, headers=headers, verify=verify)
            # Create Log
            log = {
                'name': log_name,
                'type': log_type,
                'url': url,
                'request_type': log_request_type,
                'request': log_request,
                'response_code': response.status_code,
                'response': str(response.content),
            }
            self.env['tw.api.log'].sudo().create(log)
            self._cr.commit()

            # Process Response
            if response.status_code == 200:
                content = json.loads(response.content)
                msg = content.get('message', False) or str(content)
                detail_message = content.get('detail_message', '') 
                if (str(content.get('status')) == '1' or str(content.get('status')) == 'success') and content.get('data'):
                    data = content.get('data')
                    if data:
                        return data
                    else:
                        raise Warning('Gagal mengambil status ke koprol! data tidak ada. \n' + msg + detail_message)
                else:
                    raise Warning('Gagal mengambil status ke koprol! \n' + msg + detail_message)
            else:
                try:
                    content = json.loads(response.content)
                    msg = content.get('message', False) or str(content)
                except:
                    msg = str(response.content)
                raise Warning('Failed sending data with error :' + msg)
        except Exception as e:
            raise Warning('There is an error when sending API ' + str(response.status_code) + ' : ' + str(e))

    def get_azure_access_token(self):
        """Get Azure access token using client credentials flow"""
        if not self.client_secret:
            raise Warning('Client Secret belum di setting di API Configuration.')
        
        if not self.client_id:
            raise Warning('Client ID belum di setting di API Configuration.')
        
        if not self.client_scope:
            raise Warning('Client Scope belum di setting di API Configuration.')
        
        if not self.auth_url:
            raise Warning('Auth URL belum di setting di API Configuration.')

        url = self.auth_url
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'client_id': str(self.client_id),
            'client_secret': str(self.client_secret),
            'grant_type': 'client_credentials',
            'scope': str(self.client_scope)
        }

        try:
            response = requests.post(url, headers=headers, data=payload, timeout=30)
        except requests.exceptions.RequestException as e:
            raise Warning(f"Connection Error saat mengambil Azure Token: {str(e)}")
        
        # Handle HTTP error status codes
        if response.status_code == 503:
            raise Warning("Azure Service Unavailable (503). Server sedang tidak aktif atau maintenance.")
        elif response.status_code >= 500:
            raise Warning(f"Azure Server Error (Status: {response.status_code}). Coba lagi nanti.")
        elif response.status_code >= 400:
            # Try to get error message from response
            try:
                error_data = response.json()
                error_msg = error_data.get('error_description') or error_data.get('error') or str(error_data)
            except (json.JSONDecodeError, ValueError):
                error_msg = response.text[:500] if response.text else "(empty response)"
            raise Warning(f"Azure Auth Error (Status: {response.status_code}): {error_msg}")
        
        # Try to parse JSON response safely
        try:
            response_data = response.json()
        except (json.JSONDecodeError, ValueError):
            raw_response = response.text[:500] if response.text else "(empty response)"
            raise Warning(f"Invalid JSON Response dari Azure (Status: {response.status_code}). Response: {raw_response}")
        
        token = response_data.get('access_token')
        if not token:
            raise Warning(f"Failed to get access token from Azure. Response: {response_data}")

        current_time = datetime.now()
        expires_in = response_data.get('expires_in', 3600)  # Default 1 hour if not provided
        expiration_time = current_time + timedelta(seconds=int(expires_in))

        # Save token to the API Configuration record
        self.sudo().write({'token': token, 'expired_on': expiration_time})