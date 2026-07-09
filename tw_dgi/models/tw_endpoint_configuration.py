# -*- coding: utf-8 -*-
# 1: imports of python lib

# 2: import of known third party lib
import json

# 3: imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwEndpointConfigurationDGI(models.Model):
    _inherit = "tw.endpoint.configuration"
    _description = "DGI Endpoint Configuration Extensions"

    # 7: defaults methods
    
    # 8: fields
    mode = fields.Selection([
        ('read', 'READ'),
        ('add', 'ADD') 
    ], string='DGI Mode', help="DGI operation mode") 
    output_template = fields.Json(
            string="Output Structure Template",
            help="Mapping dari raw response JSON ke struktur values Odoo.\n\n"
                "Define custom output structure using JSON template.\n\n"
                "Special keywords:\n"
                "- '_array_source': JSON path to array data\n"
                "- '_item_template': Template for each array item\n"
                "- '_from_result': Resolve value dari parsed result field lain\n"
                "- '_type': Tipe hasil resolve untuk _from_result (mis. m2o)\n"
                "- '_<field>_vals': Dict for create record when lookup fails\n\n"
                "Relational Lookup Pattern:\n"
                "  'partner_id': 'noKtp'  -> lookup via mapping\n"
                "  '_partner_vals': {     -> vals for create if not found\n"
                "    'identification_number': 'noKtp',\n"
                "    'name': 'namaCustomer',\n"
                "    'phone': 'noKontak'\n"
                "  }\n\n"
                "Array Pattern:\n"
                "  'line_ids': {\n"
                "    '_array_source': 'unit',\n"
                "    '_item_template': {'product_id': 'kodeTipeUnit'}\n"
                "  }\n\n"
                "Derived Field Pattern:\n"
                "  'partner_id': {\n"
                "    '_from_result': 'company_id.default_supplier_id',\n"
                "    '_type': 'm2o'\n"
                "  }"
        )
    
    target_model_id = fields.Many2one(
        'ir.model',
        string='Target Model',
        help="Target Odoo model for this endpoint"
    )

    dgi_division_id = fields.Many2one('tw.selection', string='Division DGI', domain=[('type', '=', 'DivisionDGI')])

    # 9: relation fields
    response_mapping_ids = fields.One2many(
        'tw.mapping.response',
        'endpoint_id',
        string='Response Mappings'
    )
    
    # 10: constraints & sql constraints
    @api.constrains('code', 'version', 'mode')
    def _check_code_version_mode(self):
        """DGI-specific constraint including mode"""
        for rec in self:
            if rec.mode and self.sudo().search([
                ('code', '=', rec.code), 
                ('version', '=', rec.version), 
                ('mode', '=', rec.mode), 
                ('config_id', '=', rec.config_id.id),
                ('id', '!=', rec.id)
            ], limit=1):
                raise UserError(_("Endpoint with same Code, Version and Mode already exists."))
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    def action_import_response_mappings(self):
        """Open wizard to import response mappings from Excel/CSV"""
        self.ensure_one()
        return {
            "name": _("Import Response Mappings"),
            "type": "ir.actions.act_window",
            "res_model": "tw.response.mapping.import.wizard",
            "view_mode": "form",
            "target": "new",
            "context": dict(self.env.context or {}, default_endpoint_id=self.id),
        }
    
    def action_open_response_mapping(self):
        """Open mapping list filtered by this endpoint (popup with form/list support)."""
        self.ensure_one()
        
        list_view_id = self.env.ref('tw_dgi.view_tw_mapping_response_list').id
        form_view_id = self.env.ref('tw_dgi.view_tw_mapping_response_form').id
        
        return {
            'name': _('Response Mappings'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.mapping.response',
            'view_mode': 'list',
            'views': [(list_view_id, 'list')],
            'target': 'new',
            'view_id': self.env.ref('tw_dgi.view_tw_endpoint_output_template_form').id,
            'domain': [('endpoint_id', '=', self.id)],
            'context': dict(self.env.context or {}, default_endpoint_id=self.id),
        }
    
    # 14: private method
    
    def action_open_config_wizard(self):
        """Open unified configuration wizard"""
        self.ensure_one()
        return {
            'name': _('Configure Endpoint'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.endpoint.config.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_endpoint_id': self.id}
        }

    def action_open_output_template_wizard(self):
        """Open form to edit output_template field"""
        self.ensure_one()
        
        # Create custom view with only output_template field
        return {
            'name': _('Configure Output Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.endpoint.configuration',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('tw_dgi.view_tw_endpoint_output_template_form').id,
            'context': {'form_view_initial_mode': 'edit'},
        }

    @api.model
    def _parse_output_template_default_value(self, default_value):
        """Convert mapping default_value string to JSON-compatible literal."""
        if default_value in ("true", "True"):
            return True
        if default_value in ("false", "False"):
            return False
        if default_value in ("null", "None"):
            return None

        try:
            return json.loads(default_value)
        except (json.JSONDecodeError, TypeError):
            return default_value

    def _build_output_template_dict(self, mappings=None):
        """Build output template dictionary from endpoint response mappings."""
        self.ensure_one()
        template = {}
        line_groups = {}
        mapping_obj = mappings or self.response_mapping_ids

        for mapping in mapping_obj:
            if mapping.field_type == "validation":
                continue

            target_field = mapping.target_field
            json_path = mapping.json_path

            if not target_field and json_path:
                target_field = f"_{json_path}"

            if not target_field:
                continue

            if mapping.line_group:
                line_groups.setdefault(mapping.line_group, {})
                line_groups[mapping.line_group][target_field] = json_path
                continue

            if mapping.field_type == "derived":
                template[target_field] = {
                    "_from_result": json_path,
                    "_type": mapping.derived_value_type or "m2o",
                }
            elif json_path == "__default__" and mapping.default_value not in (False, None, ""):
                default_value = self._parse_output_template_default_value(mapping.default_value)
                if isinstance(default_value, str):
                    template[target_field] = {"_value": default_value}
                else:
                    template[target_field] = default_value
            else:
                template[target_field] = json_path

            if mapping.create_if_not_found and mapping.create_field_mappings:
                try:
                    create_vals = json.loads(mapping.create_field_mappings)
                    template[f"_{target_field}_vals"] = create_vals
                except (json.JSONDecodeError, TypeError):
                    continue

        for group_name, group_fields in line_groups.items():
            template[group_name] = group_fields

        return template

    def _generate_output_template_json(self, mappings=None):
        """Generate output template JSON string from endpoint response mappings."""
        self.ensure_one()
        template = self._build_output_template_dict(mappings=mappings)
        return json.dumps(template, indent=4, ensure_ascii=False) if template else "{}"

    def _compile_output_template_from_mappings(self):
        """Compile and save output_template from response mappings."""
        for endpoint in self:
            endpoint.output_template = endpoint._build_output_template_dict()

    @api.model
    def _compile_inbound_output_templates(self):
        """Compile inbound DGI output templates from mapping master."""
        endpoint_obj = self.sudo().search([
            ("code", "in", ["dgi_uinb", "dgi_pinb"]),
        ])
        endpoint_obj._compile_output_template_from_mappings()
