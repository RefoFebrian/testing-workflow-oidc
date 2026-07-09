# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class TwEndpointConfiguration(models.Model):
    _name = "tw.endpoint.configuration"
    _description = "API Endpoint Configuration"
    _order = "code"

    # 8: fields
    name = fields.Char('Endpoint Name', compute='_compute_name', store=True)
    code = fields.Char('Code', required=True, help="Unique endpoint code identifier")
    version = fields.Char('Version', required=True, help="API version for this endpoint")
    url_path = fields.Char('URL Path', required=True, help="Endpoint path (e.g., /users/list)")
    base_url_override = fields.Char(
        'Base URL Override',
        help="Optional. If filled, this base URL will be used instead of the parent API Configuration's base URL.\n"
             "Use this when different endpoints have different base URL segments.\n"
             "Example: https://gvt-apigateway.daya-dms.id/ahmcbrprod/dgi-api"
    )
    # Auth Override Fields (standalone)
    auth_api_key_override = fields.Char(
        'Auth API Key Override',
        help="API Key untuk HMAC Auth override pada endpoint ini. Jika diisi akan menggantikan api_key dari API Config induk."
    )
    auth_api_secret_override = fields.Char(
        'Auth API Secret Override',
        help="API Secret untuk HMAC Auth override pada endpoint ini. Jika diisi akan menggantikan api_secret dari API Config induk."
    )
    full_url = fields.Char('Full URL', compute='_compute_full_url', store=True)
    active = fields.Boolean('Active', default=True)
    
    method = fields.Selection([
        ('get', 'GET'),
        ('post', 'POST'),
        ('put', 'PUT'),
        ('delete', 'DELETE')
    ], string='HTTP Method', default='post', required=True)
    
    # 9: relation fields
    config_id = fields.Many2one('tw.api.configuration', string='API Configuration', required=True)

    # 11: compute/depends & on change methods
    @api.depends('code', 'version')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.code}.{rec.version}" if rec.code and rec.version else ''
    
    @api.depends('config_id.base_url', 'base_url_override', 'version', 'url_path')
    def _compute_full_url(self):
        """Compute full URL, prioritizing endpoint-level base_url_override over parent config."""
        for rec in self:
            base_url = (rec.base_url_override or rec.config_id.base_url or '').rstrip('/')
            if base_url and rec.version and rec.url_path:
                url_path = rec.url_path.lstrip('/')
                rec.full_url = f"{base_url}/v{rec.version}/{url_path}"
            else:
                rec.full_url = ''
    
    # 10: constraints & sql constraints
    @api.constrains('code', 'version', 'config_id')
    def _check_code_version_unique(self):
        for rec in self:
            if self.sudo().search([
                ('code', '=', rec.code), 
                ('version', '=', rec.version), 
                ('config_id', '=', rec.config_id.id),
                ('id', '!=', rec.id)
            ], limit=1):
                raise UserError(_("Endpoint with same Code and Version already exists for this API Configuration."))
