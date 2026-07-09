# -*- coding: utf-8 -*-
import json
import logging
import operator as op
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class TWDGIEngine(models.AbstractModel):
    """
    TW DGI Processing Engine untuk handle business logic
    Engine untuk parse response dan handle relational lookup
    Request body akan dibuild di wizard/form masing-masing
    """
    _name = "tw.dgi.engine"
    _description = "TW DGI Processing Engine"
    
    # ========================================
    # Response Parsing Methods
    # ========================================

    def _get_output_template(self, endpoint):
        """Return output template, preferring master mappings when available."""
        if endpoint.response_mapping_ids:
            return endpoint._build_output_template_dict()
        return endpoint.output_template
    
    def parse_response(self, endpoint, response_json, target_model=None,
                        target_record=None):
        """
        Parse response dan create/update Odoo records with dynamic array handling

        Args:
            endpoint: tw.endpoint.configuration record
            response_json: dict dari API response
            target_model: optional target model name
            target_record: optional existing record untuk update

        Returns:
            dict or list of dicts: values dictionary/dictionaries ready for create/write
            Caller is responsible for creating/updating records based on business logic
        """
        template = self._get_output_template(endpoint)
        if not template:
            raise UserError(f"Output template not configured for endpoint {endpoint.code}")

        return self.apply_output_template(
            response_json,
            template,
            endpoint=endpoint
        )
    
    # Cache for parsed JSON paths to avoid repeated string operations
    _path_cache = {}

    def _is_empty_value(self, value):
        """Return True only for values that should be treated as empty by DGI parsing."""
        if value is None or value is False:
            return True
        if isinstance(value, str):
            return not value.strip()
        if isinstance(value, (list, tuple, dict, set)):
            return not value
        return False
    
    def _parse_path_component(self, component):
        """Parse a single path component into field name and optional index
        
        Returns:
            tuple: (field_name, index or None, is_wildcard)
        
        Examples:
            'unit' → ('unit', None, False)
            'unit[0]' → ('unit', 0, False)
            '*' → ('*', None, True)
        """
        if component == '*':
            return ('*', None, True)
        
        if '[' in component and ']' in component:
            field_name = component[:component.index('[')]
            index_str = component[component.index('[')+1:component.index(']')]
            index = int(index_str) if index_str.isdigit() else None
            return (field_name, index, False)
        
        return (component, None, False)
    
    def _get_parsed_path(self, json_path):
        """Get cached parsed path or parse and cache it
        
        Returns:
            list of tuples: [(field_name, index, is_wildcard), ...]
        """
        if json_path not in self._path_cache:
            components = json_path.split('.')
            self._path_cache[json_path] = [
                self._parse_path_component(comp) for comp in components
            ]
        return self._path_cache[json_path]
    
    def _extract_json_value(self, data, json_path):
        """Extract value from JSON using dotted path with array support (OPTIMIZED)
        
        Performance optimizations:
        - Path parsing cached to avoid repeated string operations
        - Early returns for None values
        - Efficient array/dict type checking
        
        Supports:
        - Simple path: 'field.subfield'
        - Array index: 'unit[0].nomorMesin'
        - First item shorthand: 'unit.nomorMesin' → auto gets unit[0].nomorMesin
        - Wildcard: 'unit.*.nomorMesin' → returns list of all values
        """
        if not data:
            return None
        
        try:
            current = data
            parsed_path = self._get_parsed_path(json_path)
            
            for i, (field_name, index, is_wildcard) in enumerate(parsed_path):
                # Handle wildcard: collect from all array items
                if is_wildcard:
                    if not isinstance(current, list):
                        return None
                    
                    # Get remaining path after wildcard
                    if i == len(parsed_path) - 1:
                        return current
                    
                    remaining_components = parsed_path[i+1:]
                    remaining_path = '.'.join([
                        f"{fn}[{idx}]" if idx is not None else fn 
                        for fn, idx, _ in remaining_components
                    ])
                    
                    # Extract from all items
                    results = []
                    for item in current:
                        value = self._extract_json_value(item, remaining_path)
                        if value is not None:
                            results.append(value)
                    return results if results else None
                
                # Handle array index notation
                if index is not None:
                    # Get the array
                    if isinstance(current, dict):
                        current = current.get(field_name)
                    else:
                        return None
                    
                    if not isinstance(current, list) or index >= len(current):
                        return None
                    
                    current = current[index]
                
                # Regular field access (no index)
                else:
                    if isinstance(current, dict):
                        current = current.get(field_name)
                    elif isinstance(current, list):
                        # Auto-access first item if current is array
                        if len(current) == 0:
                            return None
                        if isinstance(current[0], dict):
                            current = current[0].get(field_name)
                        else:
                            return None
                    else:
                        return None
                
                # Early return if None found
                if current is None:
                    return None
            
            return current
            
        except Exception as e:
            raise UserError(f"Error extracting JSON value from path '{json_path}': {str(e)}")
    
    def validate_response_field(self, mapping, value, record, custom_field_label=None):
        """
        Validate field value dengan business logic
        
        Override method ini atau tambah custom validation
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        # Basic required validation
        if mapping.is_required and self._is_empty_value(value):
            field_label = custom_field_label or mapping.json_path
            return (False, f"Field '{field_label}' is required but got empty value")
        
        # Placeholder untuk custom validation
        # Developer bisa tambah business logic disini
        # Contoh: check transaksi sebelumnya, stock check, dll
        
        return (True, '')
    
    def _apply_value_alias(self, mapping, value):
        """Helper to apply value_alias normalization for any field type"""
        if not mapping.value_alias:
            return value
            
        try:
            alias_map = json.loads(mapping.value_alias)
            if isinstance(alias_map, dict):
                normalized = alias_map.get(str(value))
                if normalized is not None:
                    _logger.debug(
                        "value_alias: '%s' → '%s' for mapping %s",
                        value, normalized, mapping.json_path
                    )
                    return normalized
        except (json.JSONDecodeError, TypeError) as e:
            _logger.warning("Invalid value_alias JSON on mapping '%s': %s", mapping.json_path, str(e))
            
        return value

    def transform_value(self, mapping, value, record):
        """
        Transform value sebelum di-assign ke Odoo field
        
        Override method ini atau tambah custom transformation
        
        Returns:
            transformed value
        """
        if self._is_empty_value(value):
            return mapping.default_value or value

        # --- Value Alias normalization for ALL fields ---
        value = self._apply_value_alias(mapping, value)
        
        # Auto convert DD/MM/YYYY to YYYY-MM-DD for date compatibility
        if isinstance(value, str) and len(value) == 10 and value[2] == '/' and value[5] == '/':
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(value, "%d/%m/%Y")
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        return value
    
    def _check_validation_filter(self, mapping, value):
        """Check if value matches filter criteria for validation fields
        
        Args:
            mapping: response mapping record with validation config
            value: extracted value from JSON
            
        Returns:
            tuple: (should_filter: bool, message: str)
            - (True, msg) = SKIP this record (doesn't match filter)
            - (False, '') = KEEP this record (matches filter)
        """
        # Only process validation fields
        if mapping.field_type != 'validation':
            return (False, '')
        
        # No filter specified - keep record
        if not mapping.expected_value:
            return (False, '')
        
        operator = mapping.validation_operator or '='
        expected = mapping.expected_value
        actual = str(value) if value is not None else ''
        
        # Perform comparison based on operator
        try:
            if operator == '=':
                matches = actual == expected
            elif operator == '!=':
                matches = actual != expected
            elif operator == 'in':
                expected_list = [v.strip() for v in expected.split(',')]
                matches = actual in expected_list
            elif operator == 'contains':
                matches = expected.lower() in actual.lower()
            elif operator in ('>', '<', '>=', '<='):
                # Numeric comparison using safe operator mapping
                try:
                    ops = {'>': op.gt, '<': op.lt, '>=': op.ge, '<=': op.le}
                    matches = ops[operator](float(actual), float(expected))
                except (ValueError, TypeError):
                    matches = False
            else:
                # Unknown operator, don't filter
                matches = True
        except Exception as e:
            raise UserError(f"Error in validation filter: {str(e)}")
        
        # Invert: if doesn't match, should filter (skip)
        should_filter = not matches
        
        if should_filter:
            msg = f"{mapping.json_path}={actual} (expected {operator} {expected})"
        else:
            msg = ''
        
        return (should_filter, msg)
    
    def lookup_relation(self, mapping, value, response_json=None):
        """
        Handle relational lookup with context, fallback, and auto-create support.

        Applies value_alias normalization before lookup: useful when the external
        API sends inconsistent formats (e.g., 'CREDIT', 'credit', '2') while the
        internal master data uses a standard format (e.g., 'Credit').

        Args:
            mapping: tw.mapping.response record
            value: Value to search for
            response_json: Current JSON item being processed (for domain context)

        Returns:
            int: record id or False
        """
        if not mapping.relation_model or not value:
            return False

        response_json = response_json or {}

        # --- Value Alias normalization sudah ditangani di transform_value() ---
        # Method transform_value() selalu dipanggil sebelum lookup_relation()
        # Namun untuk safety jika lookup_relation dipanggil terpisah, kita panggil lagi
        value = self._apply_value_alias(mapping, value)

        # Build eval context for domain expressions
        eval_context = {
            'today': fields.Date.today(),
            'value': value,
        }
        if isinstance(response_json, dict):
            eval_context.update(response_json)

        try:
            relation_model = self.env[mapping.relation_model].sudo()

            # Build primary search domain
            domain = [(mapping.relation_lookup_field, '=', value)]
            if mapping.relation_search_domain:
                try:
                    additional_domain = safe_eval(mapping.relation_search_domain, eval_context)
                    domain += additional_domain
                except Exception as e:
                    raise UserError(
                        f"Error parsing relation_search_domain for {mapping.json_path}: {str(e)}"
                    )

            # Search with primary domain
            relation_record = relation_model.search(domain, limit=1)

            # Try fallback domain if no result
            if not relation_record and mapping.fallback_domain:
                try:
                    fallback_domain = safe_eval(mapping.fallback_domain, eval_context)
                    fallback_full_domain = [
                        (mapping.relation_lookup_field, '=', value)
                    ] + fallback_domain
                    relation_record = relation_model.search(fallback_full_domain, limit=1)
                except Exception as e:
                    raise UserError(
                        f"Error parsing fallback_domain for {mapping.json_path}: {str(e)}"
                    )

            # Auto-create if not found and create_if_not_found is enabled
            if not relation_record and mapping.create_if_not_found:
                relation_record = self._create_relation_record(
                    mapping, value, response_json, eval_context
                )

            if relation_record:
                return relation_record.id
            else:
                if mapping.is_required:
                    raise UserError(
                        f"Data for '{mapping.json_path}' with value '{value}' not found"
                    )
                return False

        except UserError:
            raise
        except Exception as e:
            raise UserError(f"Error in relation lookup for {mapping.json_path}: {str(e)}")

    def _create_relation_record(self, mapping, value, response_json, eval_context):
        """
        Create relation record when not found and create_if_not_found is enabled.

        Supports extended create_field_mappings format:
        - String: Extract from JSON path ("name": "namaCustomer")
        - Number/Bool: Static value ("customer_rank": 1)
        - Dict with _lookup: Lookup relation and format
            {
                "_lookup": "res.partner.category",
                "_field": "name",
                "_value": "Customer",
                "_type": "m2m"  # m2m, m2o, or o2m
            }

        Args:
            mapping: tw.mapping.response record with create_field_mappings
            value: Original lookup value
            response_json: Source JSON data for field extraction
            eval_context: Context for eval expressions

        Returns:
            Created record or False
        """
        if not mapping.create_field_mappings:
            return False

        try:
            field_mappings = json.loads(mapping.create_field_mappings)
        except (json.JSONDecodeError, TypeError):
            return False

        # Build create vals from response_json
        create_vals = {}
        for field_name, field_config in field_mappings.items():
            if isinstance(field_config, str):
                # Extract value from JSON path
                field_value = self._extract_json_value(response_json, field_config)
                if field_value is not None:
                    create_vals[field_name] = field_value
            elif isinstance(field_config, dict) and '_lookup' in field_config:
                # Lookup relation field
                lookup_value = self._resolve_lookup_config(field_config, response_json)
                if lookup_value is not None:
                    create_vals[field_name] = lookup_value
            else:
                # Static value (number, bool, etc)
                create_vals[field_name] = field_config

        # Always include the lookup field with original value if not already set
        if mapping.relation_lookup_field and value and mapping.relation_lookup_field not in create_vals:
            # If the lookup field is explicitly defined in create_field_mappings, do not fallback to the search key
            if mapping.relation_lookup_field not in field_mappings:
                create_vals[mapping.relation_lookup_field] = value

        if not create_vals:
            return False

        try:
            relation_model = self.env[mapping.relation_model].sudo()
            new_record = relation_model.create(create_vals)
            return new_record
        except Exception as e:
            error_msg = str(e)
            raise UserError(
                f"Gagal membuat data otomatis pada model '{mapping.relation_model}'.\n"
                f"Hal ini biasanya karena ada field relasi (lookup) yang wajib diisi namun datanya tidak ditemukan di Odoo.\n"
                f"Data yang berhasil diproses sebelum error: {create_vals}\n\n"
                f"Pesan Sistem: {error_msg}"
            )

    def _resolve_lookup_config(self, config, response_json):
        """
        Resolve lookup config dict to actual field value.

        Config format:
        {
            "_lookup": "model.name",
            "_field": "field_to_search",
            "_value": "value_or_json_path",
            "_type": "m2m" | "m2o" | "o2m"
        }

        Returns:
            - m2m: [(6, 0, [ids])]
            - m2o: record_id (int)
            - o2m: [(0, 0, {...})] - not yet implemented
        """
        model_name = config.get('_lookup')
        search_field = config.get('_field', 'name')
        value_or_path = config.get('_value', '')
        field_type = config.get('_type', 'm2o')

        if not model_name:
            return None

        # Resolve value - could be static or JSON path
        if isinstance(value_or_path, str):
            # Try as JSON path first (dotted path or simple key)
            search_value = self._extract_json_value(response_json, value_or_path)
            if search_value is None:
                search_value = value_or_path  # Use as static if not found

        if not search_value:
            return None

        try:
            lookup_model = self.env[model_name].sudo()
            records = lookup_model.search([(search_field, '=', search_value)])
        except Exception as e:
            _logger.error(
                "Error resolving lookup config for model %s, field %s, value %s: %s",
                model_name, search_field, search_value, str(e)
            )
            return None

        if not records:
            # Jika nilai yang dicari persis sama dengan nama JSON path dan tidak ditemukan di payload JSON,
            # kemungkinan ini adalah optional field yang dikosongkan oleh API. Abaikan (return None).
            if isinstance(value_or_path, str) and search_value == value_or_path and self._extract_json_value(response_json, value_or_path) is None:
                return None

            try:
                model_desc = lookup_model._description or model_name
                field_desc = lookup_model._fields[search_field].string if search_field in lookup_model._fields else search_field
            except Exception:
                model_desc = model_name
                field_desc = search_field

            raise UserError(
                f"Data master tidak ditemukan!\n"
                f"Sistem gagal mencari '{model_desc}' "
                f"yang memiliki '{field_desc}' = '{search_value}'.\n"
                f"Harap tambahkan atau perbaiki data master tersebut di Odoo agar proses integrasi dapat dilanjutkan."
            )

        if field_type == 'm2m':
            return [(6, 0, records.ids)]
        elif field_type == 'm2o':
            return records[0].id
        else:
            return None
    
    # ========================================
    # Template-Based Output Structuring
    # ========================================
    
    def apply_output_template(self, response_json, template, endpoint=None,
                               parent_path=""):
        """Apply JSON template to transform data structure

        Args:
            response_json: Original API response (dict)
            template: Output template configuration (dict)
            endpoint: Optional endpoint config for validation/mapping lookup
            parent_path: Current JSON path context (for nested mapping lookup)

        Returns:
            Structured dictionary matching template
        """
        if not template:
            raise UserError(f"Output template not configured for endpoint {endpoint.code}")
        
        # Ensure template is a dict
        if isinstance(template, str):
            try:
                template = json.loads(template)
            except json.JSONDecodeError as e:
                raise UserError(f"Invalid JSON in output template for endpoint {endpoint.code}: {str(e)}")
        
        if not isinstance(template, dict):
            raise UserError(f"Output template must be a JSON object (dict), got {type(template)} for endpoint {endpoint.code}")
        
        # Pre-fetch mappings if endpoint provided for faster lookup
        mappings = {}
        if endpoint and endpoint.response_mapping_ids:
            # Index by json_path (source field) instead of target_field
            mappings = {m.json_path: m for m in endpoint.response_mapping_ids}
        
        result = {}
        for target_field, config in template.items():
            # Handle line group dict (auto-detect array from dot notation paths)
            if isinstance(config, dict) and not any(k.startswith('_') for k in config.keys()):
                # Detect array source from first field's json_path (e.g., "unit.kodeTipeUnit" -> "unit")
                field_mappings = config
                array_source = None
                
                # Find common array source from json paths
                # Find common array source from json paths
                for json_path in field_mappings.values():
                    if isinstance(json_path, str) and '.' in json_path:
                        potential_source = json_path.split('.')[0]
                        if array_source is None:
                            array_source = potential_source
                        elif array_source != potential_source:
                            # Mixed sources - not a valid line group
                            array_source = None
                            break
                
                if array_source:
                    # This is a line group - process as array
                    array_data = self._extract_json_value(response_json, array_source)
                    
                    if not isinstance(array_data, list):
                        array_data = [array_data] if array_data else []
                    
                    current_array_path = f"{parent_path}.{array_source}" if parent_path else array_source
                    
                    processed_lines = []
                    for idx, item in enumerate(array_data):
                        line_vals = {}
                        skip_line = False
                        item_context = dict(response_json)
                        if isinstance(item, dict):
                            item_context.update(item)
                            value = self._extract_json_value(item, item_path)
                            # Fallback: jika value tidak ditemukan di item dan json_path
                            # bukan sub-field dari array_source (misal 'idSPK' bukan 'unit.idSPK'),
                            # coba ambil dari item_context yang sudah include parent response.
                            # Ini memungkinkan root-level fields (idSPK, idSO, dll) digunakan
                            # dalam line group mapping — misalnya dealer yang tidak kirim
                            # nomorRangka di tiap unit (Wahana) dikonfigurasi pakai idSPK.
                            if value is None and not json_path.startswith(f"{array_source}."):
                                value = self._extract_json_value(item_context, json_path)
                            
                            # Smart mapping lookup using full original path
                            mapping = mappings.get(json_path)
                            
                            # Only apply mapping if target_field matches current key
                            # This allows reusing same json_path for different fields (as raw value)
                            if mapping and mapping.target_field and mapping.target_field != field_name:
                                mapping = None
                            
                            if mapping:
                                # Validation filter: skip entire line if value doesn't match
                                if mapping.field_type == 'validation':
                                    should_filter, filter_msg = self._check_validation_filter(
                                        mapping, value
                                    )
                                    if should_filter:
                                        _logger.info(
                                            "Validation filter skipped line %d: %s",
                                            idx, filter_msg
                                        )
                                        skip_line = True
                                        break
                                    # Don't add validation-only fields to output
                                    continue
                                
                                value = self.transform_value(mapping, value, None)
                                is_valid, error_msg = self.validate_response_field(
                                    mapping, value, None, custom_field_label=json_path
                                )
                                if not is_valid and mapping.is_required:
                                    raise UserError(f"Required field {field_name} ({json_path}) is missing or invalid: {error_msg}")
                                
                                if mapping.field_type == 'relation':
                                    # Merge parent response context for domain eval
                                    # (e.g., idSPK accessible for lot lookup domain)
                                    value = self.lookup_relation(mapping, value, item_context)
                            
                            line_vals[field_name] = value
                        
                        if skip_line:
                            continue
                        
                        # Hook for custom line processing
                        line_vals = self._prepare_line_vals(
                            target_field, line_vals, item, idx, endpoint
                        )
                        
                        if line_vals:
                            processed_lines.append((0, 0, line_vals))
                    
                    if processed_lines:
                        result[target_field] = processed_lines
                else:
                    # Not a line group - treat as nested object
                    nested_result = self.apply_output_template(
                        response_json, config, endpoint=endpoint, parent_path=parent_path
                    )
                    if nested_result:
                        result[target_field] = nested_result
            
            # Handle legacy _array_source format (backward compatibility)
            elif isinstance(config, dict) and '_array_source' in config:
                array_source = config['_array_source']
                array_data = self._extract_json_value(response_json, array_source)
                
                if not isinstance(array_data, list):
                    array_data = [array_data] if array_data else []
                
                item_template = config.get('_item_template', {})
                current_array_path = f"{parent_path}.{array_source}" if parent_path else array_source
                
                processed_array = []
                for item in array_data:
                    processed_item = self.apply_output_template(
                        item,
                        item_template,
                        endpoint=endpoint,
                        parent_path=current_array_path
                    )
                    if processed_item:
                        processed_array.append((0, 0, processed_item))
                
                if processed_array:
                    result[target_field] = processed_array
                    
            elif isinstance(config, dict) and '_value' in config:
                result[target_field] = config.get('_value')

            elif isinstance(config, dict) and '_from_result' in config:
                result[target_field] = self._resolve_inline_derived_value(
                    endpoint, result, target_field, config
                )

            elif isinstance(config, dict):
                # Nested object (not array)
                nested_result = self.apply_output_template(
                    response_json,
                    config,
                    endpoint=endpoint,
                    parent_path=parent_path
                )
                if nested_result:
                    result[target_field] = nested_result
                    
            elif isinstance(config, str):
                # Simple field mapping: 'target_field': 'json.path'
                json_path = config
                value = self._extract_json_value(response_json, json_path)
                
                # Smart Mapping Lookup
                mapping = None
                absolute_path = f"{parent_path}.{json_path}" if parent_path else json_path
                
                if absolute_path in mappings:
                    mapping = mappings[absolute_path]
                elif json_path in mappings:
                    mapping = mappings[json_path]
                
                # Check mapping target match
                if mapping and mapping.target_field and mapping.target_field != target_field:
                    # Allow mismatch if target_field is empty (generic mapping)
                    # But strict check if configured
                    mapping = None

                if mapping:
                    value = self.transform_value(mapping, value, None)
                    is_valid, error_msg = self.validate_response_field(mapping, value, None, custom_field_label=absolute_path)
                    if not is_valid:
                        if mapping.is_required:
                            raise UserError(f"Required field {target_field} ({absolute_path}) is missing or invalid: {error_msg}")
                        else:
                            continue
                    
                    if mapping.field_type == 'relation':
                        value = self.lookup_relation(mapping, value, response_json)
                
                result[target_field] = value
            else:
                # Static literal value from output template
                result[target_field] = config

        return result

    def _resolve_inline_derived_value(self, endpoint, values, target_field, config):
        """Resolve a single derived field from parsed result values."""
        if not isinstance(config, dict):
            raise UserError(
                f"Invalid derived config for field '{target_field}' in endpoint {endpoint.code}"
            )

        from_result = config.get('_from_result')
        field_type = config.get('_type', 'm2o')

        if not from_result or not isinstance(from_result, str):
            raise UserError(
                f"Derived field '{target_field}' in endpoint {endpoint.code} must define "
                f"a string '_from_result'"
            )

        if field_type != 'm2o':
            raise UserError(
                f"Derived field '{target_field}' in endpoint {endpoint.code} has unsupported "
                f"type '{field_type}'"
            )

        record = self._resolve_result_path_to_record(endpoint, values, from_result)
        return record.id if record else False

    def _resolve_result_path_to_record(self, endpoint, values, result_path):
        """Resolve a dotted path from parsed values to an Odoo record."""
        target_model_name = endpoint.target_model_id.model
        if not target_model_name:
            raise UserError(
                f"Endpoint {endpoint.code} must define target_model_id to resolve derived fields"
            )

        path_components = result_path.split('.')
        if not path_components or not path_components[0]:
            raise UserError(
                f"Invalid derived path '{result_path}' for endpoint {endpoint.code}"
            )

        root_field = path_components[0]
        target_model = self.env[target_model_name]
        root_field_obj = target_model._fields.get(root_field)
        if not root_field_obj:
            raise UserError(
                f"Invalid derived path '{result_path}' for endpoint {endpoint.code}: "
                f"field '{root_field}' not found on model {target_model_name}"
            )

        root_value = values.get(root_field)
        if not root_value:
            return False

        if root_field_obj.type != 'many2one':
            raise UserError(
                f"Invalid derived path '{result_path}' for endpoint {endpoint.code}: "
                f"root field '{root_field}' must be many2one"
            )

        if not isinstance(root_value, int):
            raise UserError(
                f"Invalid derived path '{result_path}' for endpoint {endpoint.code}: "
                f"root field '{root_field}' must resolve to an integer id"
            )

        current_record = self.env[root_field_obj.comodel_name].browse(root_value)
        if not current_record.exists():
            return False

        for field_name in path_components[1:]:
            current_field_obj = current_record._fields.get(field_name)
            if not current_field_obj:
                raise UserError(
                    f"Invalid derived path '{result_path}' for endpoint {endpoint.code}: "
                    f"field '{field_name}' not found on model {current_record._name}"
                )

            current_record = current_record[field_name]
            if not current_record:
                return False

            if not isinstance(current_record, models.BaseModel):
                raise UserError(
                    f"Invalid derived path '{result_path}' for endpoint {endpoint.code}: "
                    f"field '{field_name}' must resolve to a relational record"
                )

        return current_record

    def _prepare_line_vals(self, line_field, vals, source_item, index, endpoint):
        """Hook method for custom line processing
        
        Override this method in child class to add custom logic for line vals.
        
        Args:
            line_field: Target field name for lines (e.g., 'line_ids', 'spk_lines')
            vals: Processed line values dictionary
            source_item: Original JSON item from array
            index: Index of current item in array
            endpoint: Endpoint configuration record
        
        Returns:
            dict: Modified vals dictionary (or None to skip this line)
        
        Example override:
            def _prepare_line_vals(self, line_field, vals, source_item, index, endpoint):
                vals = super()._prepare_line_vals(line_field, vals, source_item, index, endpoint)
                if line_field == 'line_ids':
                    vals['note'] = f"Imported from DGI index {index}"
                return vals
        """
        return vals
