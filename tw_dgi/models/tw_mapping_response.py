# -*- coding: utf-8 -*-
# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwMappingResponse(models.Model):
    _name = "tw.mapping.response"
    _description = "Response Field Mapping Configuration"
    _order = "sequence, id"

    # 7: defaults methods

    # 8: fields
    sequence = fields.Integer(default=10)
    json_path = fields.Char(
        string="JSON Path", 
        required=True, 
        help="e.g., data.0.name or status"
    )
    
    field_type = fields.Selection([
        ("direct", "Direct Mapping"),
        ("relation", "Relational Lookup"),
        ("validation", "Validation Only"),
        ("derived", "Derived Field")
    ], required=True, default="direct", 
       help="Validation type will extract and validate without saving")
    
    is_required = fields.Boolean(string="Required Field")
    default_value = fields.Char(string="Default Value")
    notes = fields.Text(string="Notes")
    
    # Target Field - nama field Odoo tujuan
    target_field = fields.Char(
        string="Target Field",
        help="Nama field Odoo tujuan, e.g., partner_id, company_id, sales_id"
    )
    
    # Line Group - untuk grouping array items
    line_group = fields.Char(
        string="Line Group",
        help="Nama group untuk line items array (e.g., spk_lines, accessory_lines). "
             "Kosongkan untuk field header."
    )
    
    # Fallback Create Configuration
    create_if_not_found = fields.Boolean(
        string="Create if Not Found",
        default=False,
        help="Jika True, buat record baru kalau lookup gagal"
    )
    create_field_mappings = fields.Text(
        string="Create Field Mappings",
        help='JSON mapping untuk create record baru jika lookup gagal.\n'
             'Format yang didukung:\n'
             '- String: Extract dari JSON path → "name": "namaCustomer"\n'
             '- Number/Bool: Static value → "customer_rank": 1\n'
             '- Lookup dict: Untuk field relasi\n'
             '  "category_id": {\n'
             '    "_lookup": "res.partner.category",\n'
             '    "_field": "name",\n'
             '    "_value": "Customer",\n'
             '    "_type": "m2m"  (m2m, m2o)\n'
             '  }'
    )
    validation = fields.Selection([
        ("required", "Required"),
        ("unique", "Unique"),
        ("reference", "Reference")
    ])
    
    # Validation Filter Fields (for filtering data)
    expected_value = fields.Char(
        string="Expected Value",
        help="For validation fields: expected value to filter records. E.g., '8' for statusFakturSTNK=8"
    )
    validation_operator = fields.Selection([
        ('=', 'Equals'),
        ('!=', 'Not Equals'),
        ('in', 'In (comma-separated)'),
        ('>', 'Greater Than'),
        ('<', 'Less Than'),
        ('>=', 'Greater or Equal'),
        ('<=', 'Less or Equal'),
        ('contains', 'Contains')
    ], string="Validation Operator", default='=',
        help="Operator for validation check")
    
    # Enhanced Relational Mapping Fields
    relation_search_domain = fields.Char(
        string="Search Domain",
        help="Additional domain filter, e.g., [('active','=',True)]"
    )
    
    relation_lookup_field = fields.Char(
        string="Lookup Field",
        help="Field in relation model to match against (e.g., external_id, code)"
    )

    fallback_domain = fields.Char(
        string="Fallback Domain",
        help="Secondary domain to try if primary search returns no results. "
             "Supports context vars: branch_id, today. "
             "Example: [('job_id.name','in',['Sales Digital'])]"
    )

    value_alias = fields.Text(
        string="Value Alias (External → Internal)",
        help='JSON mapping untuk normalisasi nilai eksternal ke nilai internal sebelum lookup.\n'
             'Berguna saat API mengirim format tidak konsisten (CREDIT, credit, 2)\n'
             'tapi master data menggunakan format berbeda (Credit).\n'
             'Format: {"nilai_eksternal": "nilai_internal"}\n'
             'Contoh: {"CREDIT": "Credit", "credit": "Credit", "2": "Credit", "CASH": "Cash", "1": "Cash"}'
    )
    derived_value_type = fields.Selection([
        ("m2o", "Many2one"),
    ], string="Derived Value Type", default="m2o",
       help="Type hasil resolusi untuk field turunan")
    
    # 9: relation fields
    relation_model_id = fields.Many2one(
        "ir.model",
        string="Relation Model",
        ondelete="cascade",
        help="Model to lookup relation from"
    )
    relation_model = fields.Char(
        string="Relation Model Name",
        related="relation_model_id.model",
        store=True,
        readonly=True
    )
    
    endpoint_id = fields.Many2one(
        "tw.endpoint.configuration", 
        string="Endpoint", 
        ondelete="cascade"
    )
    
    # 10: constraints & sql constraints
    @api.constrains('field_type', 'expected_value', 'create_if_not_found', 'create_field_mappings')
    def _check_field_requirements(self):
        """Check field requirements based on field_type and create settings"""
        for rec in self:
            # Validation type: expected_value required
            if rec.field_type == 'validation':
                if not rec.expected_value:
                    raise ValidationError(
                        "Field 'Expected Value' is required when Field Type is 'Validation Only'.\n"
                        "This value is used to filter which records to import."
                    )
            # Relation type with create_if_not_found: create_field_mappings required
            if rec.create_if_not_found and not rec.create_field_mappings:
                raise ValidationError(
                    "Field 'Create Field Mappings' is required when 'Create if Not Found' is checked.\n"
                    "Please configure the JSON mapping for creating new records."
                )
            if rec.field_type == 'derived' and not rec.target_field:
                raise ValidationError(
                    "Field 'Target Field' is required when Field Type is 'Derived Field'."
                )
    
    # 11: compute/depends & on change methods
    @api.onchange('field_type')
    def _onchange_field_type(self):
        """Set defaults and clear unused fields based on field_type"""
        if self.field_type == 'validation':
            # Set default operator for validation
            if not self.validation_operator:
                self.validation_operator = '='
        else:
            # Clear validation fields if not validation type
            self.expected_value = False
            self.validation_operator = False

        if self.field_type != 'relation':
            self.relation_model_id = False
            self.relation_lookup_field = False
            self.relation_search_domain = False
            self.fallback_domain = False
            self.create_if_not_found = False
            self.create_field_mappings = False
    
    # 12: override methods
    
    # 13: action methods
    def action_show_mapping_guide(self):
        """Open guide wizard with mapping instructions."""
        return {
            'name': 'Mapping Configuration Guide',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.mapping.response',
            'view_mode': 'form',
            'view_id': self.env.ref('tw_dgi.view_tw_mapping_response_form').id,
            'target': 'new',
            'context': {'create': False, 'edit': False, 'delete': False},
        }

    def action_open_rules(self):
        """Open Rules popup form for advanced configuration."""
        self.ensure_one()
        return {
            'name': 'Mapping Rules',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.mapping.response',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('tw_dgi.view_tw_mapping_response_rules_form').id,
            'target': 'new',
            'flags': {'mode': 'edit'},
        }

    # 14: private method
