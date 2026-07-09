# 1: imports of python lib
import requests
import json
import hashlib
from datetime import datetime
import base64

# 2: import of known third party lib
from requests_toolbelt.multipart.encoder import MultipartEncoder

# 3:  imports of odoo
from odoo import api, fields, models
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class ApiConfiguration(models.Model):
    _name = "tw.api.configuration"
    _description = "API Configuration"

    # 7: defaults methods
    def _get_default_company(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False

    # 8: fields
    name = fields.Char('API Name')
    base_url = fields.Char('Base URL')
    username = fields.Char('Username')
    password = fields.Char('Password')
    api_key = fields.Char('API Key')
    api_secret = fields.Char('API Secret')
    token = fields.Char('Token')
    client_id = fields.Char('Client ID')
    client_secret = fields.Char('Client Secret')
    client_scope = fields.Char('Client Scope')
    api_type_value = fields.Char(related='api_type_id.value', string='API Type Value')
    auth_url = fields.Char('Auth Url')
    tenant_id = fields.Char(string='Tenant ID')
    expired_on = fields.Datetime('Expired On')
    code = fields.Char(string='Code')

    auth_type = fields.Selection([
        ('basic', 'Basic Auth'),
        ('hmac', 'HMAC Auth'),
        ('provider', 'Provider Auth'),
    ], string='Auth Type')
    oauth_provider_id = fields.Many2one(
        'auth.oauth.provider', 
        string='OAuth Provider',
        help='Select the OAuth provider (e.g., Azure AD, Google, Okta)'
    )
    
    # Header Mapping Configuration (Flexible JSON approach)
    header_mapping = fields.Json(
        string='Header Mapping',
        default=lambda self: {
            'api_key': 'x-api-key',
            'signature': 'x-signature',
            'timestamp': 'x-timestamp'
        },
        help="Map internal keys to actual HTTP header names. "
             "Keys: api_key, signature, timestamp. "
             "Example for DGI: {'api_key': 'DGI-API-Key', 'signature': 'DGI-API-Token', 'timestamp': 'X-Request-Time'}"
    )
    
    additional_headers = fields.Json(
        string='Additional Headers',
        default=lambda self: {},
        help="Additional static headers to include in all requests. "
             "Example: {'X-Custom-Header': 'value', 'X-Client-ID': 'client123'}"
    )
    
    api_type_id = fields.Many2one('tw.selection', string='API Type', domain=[('type', '=', 'ApiType')])
    company_id = fields.Many2one('res.company', string="Branch", default=_get_default_company)
    user_id = fields.Many2one('res.users', string='API User')

    # 9: relation fields
    endpoint_config_ids = fields.One2many(
        'tw.endpoint.configuration',
        'config_id',
        string="Endpoint Configurations"
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].upper()
        return super(ApiConfiguration, self).create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(ApiConfiguration, self).write(vals)

    # 13: action methods
    def action_get_token(self):
        self.ensure_one()
        url = "%s/api/auth/get_tokens" % self.base_url
        if self.auth_url:
            url = "%s%s" % (self.base_url, self.auth_url)
        
        if not self.username or not self.password:
            raise Warning("Username and Password are not set up correctly, please check your API Configuration (%s)" % self.name)
        
        multipart_data = MultipartEncoder(
            fields={
                'username': self.username,
                'password': self.password,
            }
        )

        headers = {
            'Content-Type': multipart_data.content_type,
        }
        
        try:
            request_data = requests.post(url=url, data=multipart_data, headers=headers, timeout=30)
        except requests.exceptions.RequestException as e:
            raise Warning(f"Connection Error: {str(e)}")
        
        # Handle various HTTP error status codes
        if request_data.status_code in (400, 404):
            raise Warning(f"URL Not Found (Status: {request_data.status_code})")
        elif request_data.status_code == 503:
            raise Warning("Service Unavailable (503). Server sedang tidak aktif atau maintenance.")
        elif request_data.status_code >= 500:
            raise Warning(f"Server Error (Status: {request_data.status_code}). Coba lagi nanti.")
        
        # Try to parse JSON response safely
        try:
            response_content = request_data.json()
        except (json.JSONDecodeError, ValueError):
            # Response is not valid JSON
            raw_response = request_data.text[:500] if request_data.text else "(empty response)"
            raise Warning(f"Invalid JSON Response (Status: {request_data.status_code}). Response: {raw_response}")
        
        if request_data.status_code == 200:
            self.suspend_security().write({
                'token': response_content.get('access_token'),
                'expired_on': response_content.get('expired_on')
            })
        else:
            error_msg = response_content.get('error_descrip') or response_content.get('message') or str(response_content)
            raise Warning(f'Get Token Status {request_data.status_code}, Error: {error_msg}')

    def get_api_config(self, api_type):
        api_type_obj = self.env['tw.selection'].get_selection('ApiType', api_type)
        config = self.env['tw.api.configuration'].suspend_security().search([('api_type_id', '=', api_type_obj.id)], limit=1)
        return config
    
    # 14: private methods

    def _get_endpoint(self, url_name):
        # ? Helpers method to get endpoint from ir config
        return self.env['ir.config_parameter'].sudo().get_param(url_name)
    
    def _prepare_auth_headers(self, api_key_override=None, api_secret_override=None):
        """Prepare authentication headers based on auth_type.
        
        Args:
            api_key_override: Optional API key to use instead of self.api_key (HMAC only)
            api_secret_override: Optional API secret to use instead of self.api_secret (HMAC only)
        """
        self.ensure_one()
        
        if self.auth_type == 'hmac':
            return self._prepare_hmac_headers(
                api_key_override=api_key_override,
                api_secret_override=api_secret_override,
            )
        elif self.auth_type == 'basic':
            return self._prepare_basic_headers()
        else:
            # Default to basic content-type header
            return {'Content-Type': 'application/json'}
    
    def _prepare_basic_headers(self):
        """Prepare Basic Authentication headers"""
        self.ensure_one()
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add basic auth if username/password provided
        if self.username and self.password:
            credentials = f"{self.username}:{self.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded}'
        
        # Add token if available
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        return headers
    
    def _prepare_hmac_headers(self, api_key_override=None, api_secret_override=None):
        """Prepare HMAC Authentication headers with flexible header mapping.
        
        Args:
            api_key_override: If provided, overrides self.api_key for this call.
            api_secret_override: If provided, overrides self.api_secret for this call.
        """
        self.ensure_one()
        
        # Get header mapping with fallback to defaults
        # Handle both dict and string JSON
        if self.header_mapping:
            if isinstance(self.header_mapping, str):
                try:
                    header_map = json.loads(self.header_mapping)
                except (json.JSONDecodeError, ValueError):
                    header_map = {
                        'api_key': 'x-api-key',
                        'signature': 'x-signature',
                        'timestamp': 'x-timestamp'
                    }
            elif isinstance(self.header_mapping, dict):
                header_map = self.header_mapping
            else:
                header_map = {
                    'api_key': 'x-api-key',
                    'signature': 'x-signature',
                    'timestamp': 'x-timestamp'
                }
        else:
            header_map = {
                'api_key': 'x-api-key',
                'signature': 'x-signature',
                'timestamp': 'x-timestamp'
            }
        
        # Get epoch time
        epoch_time = str(int(datetime.now().timestamp()))
        
        # Use override credentials if provided, else fall back to config values
        api_key = api_key_override or self.api_key
        api_secret = api_secret_override or self.api_secret
        
        # Create signature: SHA256(api_key + api_secret + epoch_time)
        signature_string = f"{api_key}{api_secret}{epoch_time}"
        signature = hashlib.sha256(signature_string.encode()).hexdigest()
        
        # Build headers using mapping
        headers = {
            'Content-Type': 'application/json',
            header_map.get('api_key', 'x-api-key'): api_key,
            header_map.get('signature', 'x-signature'): signature,
            header_map.get('timestamp', 'x-timestamp'): epoch_time
        }
        
        # Add any additional headers
        if self.additional_headers:
            if isinstance(self.additional_headers, str):
                try:
                    additional = json.loads(self.additional_headers)
                    headers.update(additional)
                except (json.JSONDecodeError, ValueError):
                    pass
            elif isinstance(self.additional_headers, dict):
                headers.update(self.additional_headers)
        
        return headers

    def action_call_endpoint(self, endpoint, params=None, raise_exception=True):
        """Call API endpoint with authentication
        
        Args:
            endpoint: tw.endpoint.configuration record
            params: dict of request parameters
            raise_exception: If True, raise UserError on non-200 status
            
        Returns:
            dict: API response
        """
        self.ensure_one()
        
        if not endpoint:
            raise Warning("Endpoint configuration is required!")
        
        # Build full URL
        url = f"{endpoint.full_url}"
        
        # Prepare request body
        request_body = params or {}
        
        # Log request
        api_log = self.env['tw.api.log']
        
        try:
            # Prepare auth headers; if endpoint has api_key/api_secret override, inject them
            headers = self._prepare_auth_headers(
                api_key_override=endpoint.auth_api_key_override or None,
                api_secret_override=endpoint.auth_api_secret_override or None,
            )
            
            # Make API call based on method
            if endpoint.method == 'post':
                response = requests.post(
                    url=url,
                    json=request_body,
                    headers=headers,
                    timeout=30,
                )
            elif endpoint.method == 'get':
                response = requests.get(
                    url=url,
                    params=request_body,
                    headers=headers,
                    timeout=30,
                )
            elif endpoint.method == 'put':
                response = requests.put(
                    url=url,
                    json=request_body,
                    headers=headers,
                    timeout=30,
                )
            elif endpoint.method == 'delete':
                response = requests.delete(
                    url=url,
                    json=request_body,
                    headers=headers,
                    timeout=30,
                )
            else:
                raise Warning(f"Unsupported HTTP method: {endpoint.method}")
            # Parse response
            if response.content:
                try:
                    response_data = response.json()
                except (json.JSONDecodeError, ValueError):
                    response_data = {'raw_response': response.text}
            else:
                response_data = {}

            api_log.create_api_log(
                name=f"API - {endpoint.code}",
                url=url,
                description=f"API Call: {endpoint.code}",
                ip_address=self.base_url,
                response=response_data,
                payload=request_body,
                header=headers,
                response_code=str(response.status_code),
                status_code='success' if response.status_code == 200 else 'error',
                api_type_id=self.api_type_id.id if self.api_type_id else False,
                company_id=self.company_id.id or self.env.company.id
            )
            
            # Check response status
            if raise_exception and response.status_code != 200:
                raise Warning(
                    f"API Error {response.status_code}:\n"
                    f"{response_data.get('message', 'Unknown error')}"
                )
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            # Log error
            api_log.create_api_log(
                name=f"API - {endpoint.code} (ERROR)",
                url=url,
                description=f"API Error: {str(e)}",
                ip_address=self.base_url,
                response={'error': str(e)},
                payload=request_body,
                header=headers if 'headers' in locals() else {},
                response_code='0',
                status_code='error'
            )
            raise Warning(f"API Connection Error:\n{str(e)}")
