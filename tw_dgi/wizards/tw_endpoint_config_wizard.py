# -*- coding: utf-8 -*-
# 1: imports of python lib
import json

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwEndpointConfigWizard(models.TransientModel):
    """Unified configuration wizard for DGI endpoints"""
    _name = "tw.endpoint.config.wizard"
    _description = "Endpoint Configuration Wizard"

    # 7: defaults methods

    # 8: fields
    full_url = fields.Char(
        string="Full URL",
        compute="_compute_full_url",
        readonly=True,
        help="Complete API URL (base_url + url_path)"
    )
    base_url_override = fields.Char(
        string="Base URL Override",
        help="Optional. Jika diisi, URL ini akan dipakai sebagai base URL endpoint, menggantikan API Config induk.\n"
             "Kosongkan untuk menggunakan base URL dari API Configuration."
    )
    # Auth Override Standalone Fields
    auth_api_key_override = fields.Char('Auth API Key Override')
    auth_api_secret_override = fields.Char('Auth API Secret Override')
    output_template_preview = fields.Text(
        string="Output Template Preview",
        compute="_compute_output_template_preview",
        readonly=True,
        help="Auto-generated output template dari mappings"
    )
    output_template_json = fields.Text(
        string="Current Output Template",
        help="Current saved output template (editable)"
    )

    # 9: relation fields
    endpoint_id = fields.Many2one(
        'tw.endpoint.configuration',
        string='Endpoint',
        required=True,
        ondelete='cascade'
    )
    mapping_ids = fields.One2many(
        related='endpoint_id.response_mapping_ids',
        string='Response Mappings',
        readonly=False
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.model
    def default_get(self, fields_list):
        """Load output_template, base_url_override, and auth_config_override from endpoint on wizard open"""
        res = super().default_get(fields_list)
        endpoint_id = self.env.context.get('default_endpoint_id')
        if endpoint_id:
            endpoint = self.env['tw.endpoint.configuration'].browse(endpoint_id)
            if endpoint.exists():
                # Load URL and auth override
                res['base_url_override'] = endpoint.base_url_override or False
                res['auth_api_key_override'] = endpoint.auth_api_key_override or False
                res['auth_api_secret_override'] = endpoint.auth_api_secret_override or False
                # Load output template
                if endpoint.output_template:
                    try:
                        res['output_template_json'] = json.dumps(
                            endpoint.output_template, indent=4, ensure_ascii=False
                        )
                    except (TypeError, ValueError):
                        res['output_template_json'] = str(endpoint.output_template)
                else:
                    res['output_template_json'] = '{}'
        return res

    @api.depends('endpoint_id', 'endpoint_id.full_url')
    def _compute_full_url(self):
        """Display endpoint's full URL (already computed with base_url_override priority)."""
        for rec in self:
            rec.full_url = rec.endpoint_id.full_url or ''

    @api.depends('endpoint_id', 'endpoint_id.response_mapping_ids',
                 'endpoint_id.response_mapping_ids.json_path',
                 'endpoint_id.response_mapping_ids.target_field',
                 'endpoint_id.response_mapping_ids.field_type',
                 'endpoint_id.response_mapping_ids.derived_value_type',
                 'endpoint_id.response_mapping_ids.create_if_not_found',
                 'endpoint_id.response_mapping_ids.create_field_mappings')
    def _compute_output_template_preview(self):
        for rec in self:
            generated = rec._generate_output_template()
            if generated and generated != '{}':
                rec.output_template_preview = generated
            else:
                # Fallback: show hint that target_field is needed
                rec.output_template_preview = (
                    "// Auto-generate kosong karena tidak ada mapping dengan 'Target Field' terisi.\n"
                    "// Isi kolom 'Target Field' pada Response Mappings untuk generate template.\n"
                    "{}"
                )

    @api.onchange('mapping_ids')
    def _onchange_mapping_ids(self):
        """Update preview in real-time when mappings change"""
        generated = self._generate_output_template()
        if generated and generated != '{}':
            self.output_template_preview = generated
        else:
            self.output_template_preview = (
                "// Auto-generate kosong karena tidak ada mapping dengan 'Target Field' terisi.\n"
                "// Isi kolom 'Target Field' pada Response Mappings untuk generate template.\n"
                "{}"
            )

    # 12: override methods

    # 13: action methods
    def action_apply_generated_template(self):
        """Apply the auto-generated template to endpoint and to current field"""
        self.ensure_one()
        generated = self._generate_output_template()
        if generated:
            try:
                parsed = json.loads(generated)
                self.endpoint_id.output_template = parsed
                self.output_template_json = generated
            except (json.JSONDecodeError, TypeError):
                pass
        # Stay on wizard - return action to reopen
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_save_and_close(self):
        """Save current output template, URL override, and auth override fields then close"""
        self.ensure_one()
        if self.endpoint_id:
            vals = {
                'base_url_override': self.base_url_override or False,
                'auth_api_key_override': self.auth_api_key_override or False,
                'auth_api_secret_override': self.auth_api_secret_override or False,
            }
            if self.output_template_json:
                try:
                    vals['output_template'] = json.loads(self.output_template_json)
                except (json.JSONDecodeError, TypeError):
                    pass
            self.endpoint_id.write(vals)
        return {'type': 'ir.actions.act_window_close'}

    # 14: private method
    def _generate_output_template(self):
        """Generate output_template JSON from response_mapping_ids.

        Supports:
        - Header fields (line_group empty) -> direct mapping
        - Line groups -> array structure with _array_source and _item_template
        """
        self.ensure_one()
        if not self.endpoint_id:
            return "{}"

        mappings = self.mapping_ids or self.endpoint_id.response_mapping_ids
        return self.endpoint_id._generate_output_template_json(mappings=mappings)

    def _parse_default_value(self, default_value):
        """Convert mapping default_value string to JSON-compatible literal."""
        return self.endpoint_id._parse_output_template_default_value(default_value)
