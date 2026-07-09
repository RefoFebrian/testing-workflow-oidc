# -*- coding: utf-8 -*-

# 2: import of known third party lib
import copy
import json
import re

# 3:  imports of odoo
from odoo import api, fields, models
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class ApiLog(models.Model):
    _name = "tw.api.log"
    _description = "Log API"
    _order = "id desc"
    
    # 8: fields
    name = fields.Text(string='Name')
    url = fields.Text(string='URL')
    description = fields.Text(string='Descripton')
    ip_address = fields.Text(string='IP Address')
    request = fields.Text('Request')
    response = fields.Text('Response')

    response_code = fields.Char(string='Response Code')
    status_code = fields.Char(string='Status Code')
    reference = fields.Char(string='Reference')
    transaction_id = fields.Integer(string='Transaction ID')

    request_time = fields.Datetime(string='Request Time')
    response_time = fields.Datetime(string='Response Time')
    date = fields.Datetime(string='Datetime', default=fields.Datetime.now)
    
    
    # 9: relation fields
    api_type_id =  fields.Many2one(comodel_name='tw.selection', string='API Type' , domain=[('type','=','ApiType')])
    method_id =  fields.Many2one(comodel_name='tw.selection', string='Method' , domain=[('type','=','ApiMethod')])
    model_id = fields.Many2one(comodel_name='ir.model', string="Model")
    user_id = fields.Many2one(comodel_name='res.users', string='User')
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', default=lambda self: self.env.company)
    log_detail_ids = fields.One2many(comodel_name='tw.api.log.detail', inverse_name='api_log_id',string='Log Detail')
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    def create_api_log(self, name, url, description, ip_address, response, payload, header, response_code=None, status_code=None, reference=None, transaction_id=None, api_type_id=None, method_id=None, model_id=None, company_id=None):
        """
        Creates an API log entry in the 'tw.api.log' model and its details in 'tw.api.log.detail'.

        Args:
            name (str): Name of the API log.
            url (str): API URL.
            description (str): Description of the log.
            ip_address (str): IP address of the client.
            response (dict): JSON response from the API.
            payload (dict): JSON payload sent to the API.
            header (dict): JSON header sent with the API request.
            response_code (str, optional): Response code returned by the API.
            status_code (str, optional): Status code returned by the API.
            reference (str, optional): Reference ID for the log.
            transaction_id (int, optional): Transaction ID for the API call.
            api_type_id (int, optional): ID of the API type (Many2one relation).
            method_id (int, optional): ID of the method type (Many2one relation).
            model_id (int, optional): ID of the related model (Many2one relation).

        Returns:
            record: The created `tw.api.log` record.
        """
        sanitize_logs = self._is_log_sanitization_enabled()
        safe_payload = self._sanitize_log_data(payload, sanitize_logs)
        safe_header = self._sanitize_log_data(header, sanitize_logs)
        safe_response = self._sanitize_log_data(response, sanitize_logs)

        # Create detail entries
        detail_data = [
            [0, 0, {'type': 'payload', 'value': safe_payload}],
            [0, 0, {'type': 'header', 'value': safe_header}],
            [0, 0, {'type': 'response', 'value': safe_response}],
        ]

        # Create the main log entry
        api_log_vals = {
            'name': name,
            'url': url,
            'description': description,
            'ip_address': ip_address,
            'request': str(safe_payload) if safe_payload else False,
            'response': str(safe_response) if safe_response else False,
            'response_code': response_code,
            'status_code': status_code,
            'reference': reference,
            'transaction_id': transaction_id,
            'api_type_id': api_type_id,
            'method_id': method_id,
            'model_id': model_id,
            'company_id': company_id,
            'log_detail_ids': detail_data,
        }
        api_log = self.env['tw.api.log'].sudo().create(api_log_vals)

        return api_log

    def _is_log_sanitization_enabled(self):
        # Default enabled for secure-by-default logs.
        value = self.env['ir.config_parameter'].sudo().get_param(
            'tw_api.log_sanitize_sensitive_data',
            default='1'
        )
        return str(value).strip().lower() in ('1', 'true', 'yes', 'on')

    def _sanitize_log_data(self, value, enabled=True):
        if not enabled:
            return value

        def _mask_sensitive_value(raw_value):
            # sanitizer behavior : 
            # keep first 2 + last 2 characters, mask the middle with *, 
            # and if value length is under 7 use ***masked_sensitive_data*** 
            text = '' if raw_value is None else str(raw_value)
            if len(text) < 7:
                return '***masked_sensitive_data***'
            return f"{text[:2]}{'*' * (len(text) - 4)}{text[-2:]}"

        sensitive_keys = {
            'authorization',
            'token',
            'access_token',
            'refresh_token',
            'api_key',
            'apikey',
            'api-secret',
            'api_secret',
            'secret',
            'password',
            'signature',
            'x-api-key',
            'x-signature',
            'jxid',
        }
        sensitive_key_patterns = (
            'token',
            'secret',
            'password',
            'signature',
            'api-key',
            'apikey',
            'auth',
            'jxid',
        )

        def _mask(data):
            if isinstance(data, dict):
                sanitized = {}
                for key, val in data.items():
                    normalized_key = str(key).lower()
                    if (
                        normalized_key in sensitive_keys
                        or any(pattern in normalized_key for pattern in sensitive_key_patterns)
                    ):
                        sanitized[key] = _mask_sensitive_value(val)
                    else:
                        sanitized[key] = _mask(val)
                return sanitized
            if isinstance(data, list):
                return [_mask(item) for item in data]
            return data

        if value is None:
            return {}

        data = copy.deepcopy(value)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, ValueError):
                for key in sensitive_keys:
                    key_pattern = re.escape(key)
                    # Quoted value form: key: "value"
                    data = re.sub(
                        rf'(?i)(["\']?{key_pattern}["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])',
                        lambda match: f"{match.group(1)}{_mask_sensitive_value(match.group(2))}{match.group(3)}",
                        data,
                    )
                    # Unquoted value form: key: value
                    data = re.sub(
                        rf'(?i)(["\']?{key_pattern}["\']?\s*[:=]\s*)([^,\s\}}]+)',
                        lambda match: f"{match.group(1)}{_mask_sensitive_value(match.group(2))}",
                        data,
                    )
                return data
        return _mask(data)



    def action_view_payload(self):
        return self._action_view_detail('payload')

    def action_view_header(self):
        return self._action_view_detail('header')

    def action_view_response(self):
        return self._action_view_detail('response')

    def _action_view_detail(self, detail_type):
        self.ensure_one()
        log_detail = self.env['tw.api.log.detail'].search([
            ('api_log_id', '=', self.id),
            ('type', '=', detail_type)
        ], limit=1)

        if not log_detail:
            raise Warning("Detail not found for type: %s" % detail_type)

        return {
            'type': 'ir.actions.act_window',
            'name': 'API Log Detail',
            'res_model': 'tw.api.log.detail',
            'view_mode': 'form',
            'res_id': log_detail.id,
            'target': 'new',
        }

    # 14: private methods


class ApiLogDetail(models.Model):
    _name = "tw.api.log.detail"
    _description = "Log API Detail"
    
    # 8: fields
    value = fields.Json(string='Value')
    value_formatted = fields.Text(
        string='Value Formatted',
        compute='_compute_value_formatted',
        store=False
    )
    type = fields.Selection(selection=[
        ('payload', 'Payload'),
        ('header', 'Header'),
        ('response', 'Response')
    ], string='Type')
    # 9: relation fields
    api_log_id = fields.Many2one(comodel_name='tw.api.log', string='API Log')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('value')
    def _compute_value_formatted(self):
        import json
        for record in self:
            if record.value:
                try:
                    if isinstance(record.value, str):
                        parsed = json.loads(record.value)
                    else:
                        parsed = record.value
                    record.value_formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                except (json.JSONDecodeError, TypeError):
                    record.value_formatted = str(record.value)
            else:
                record.value_formatted = ""
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
