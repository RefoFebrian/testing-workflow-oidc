# -*- coding: utf-8 -*-

import json
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, time
import logging

_logger = logging.getLogger(__name__)

class TWDGIWizardMixin(models.AbstractModel):
    """Reusable wizard mixin for DGI API integration"""
    _name = "tw.dgi.wizard.mixin"
    _description = "DGI Wizard Mixin"
    
    # DGI API Request Fields
    from_time = fields.Date(
        string="From Date",
        required=True,
        default=fields.Date.context_today,
        help="Start date for DGI query"
    )
    to_time = fields.Date(
        string="To Date",
        required=True,
        default=fields.Date.context_today,
        help="End date for DGI query"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Branch",
        required=True,
        help="Filter by branch"
    )
    id_spk = fields.Char(
        string="SPK ID",
        help="Specific SPK ID to query (optional)"
    )
    id_prospect = fields.Char(
        string="Prospect ID",
        help="Specific Prospect ID to query (optional)"
    )
    
    process_log = fields.Text(
        string="Process Log",
        readonly=True,
        help="Log of success and error messages from DGI sync"
    )
    found_count = fields.Integer("Records Found", readonly=True, default=0)
    
    @api.model
    def _get_api_config(self):
        """Get DGI API configuration from branch setting"""
        branch_setting = self.company_id.branch_setting_id
        
        if not branch_setting:
            raise UserError(f"Branch Setting not found for branch {self.company_id.name}")
        
        if not branch_setting.dgi_config_id:
            raise UserError(
                f"DGI API Configuration not set in Branch Setting for branch {self.company_id.name}!\n"
                "Please configure DGI Config in Branch Setting first."
            )
        
        return branch_setting.dgi_config_id
    
    def _prepare_api_request_body(self):
        """Build request body for DGI API call"""
        self.ensure_one()
        
        # Validate date range (max 3 days)
        date_diff = (self.to_time - self.from_time).days
        if date_diff > 3:
            raise UserError(
                "Date range is too large!\n"
                "Maximum allowed range is 3 days.\n"
                f"Current range: {date_diff} days"
            )
        
        from_datetime = datetime.combine(self.from_time, time(0, 0, 1))  # 00:00:01
        to_datetime = datetime.combine(self.to_time, time(23, 59, 59))  # 23:59:59
        
        body = {
            "fromTime": from_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "toTime": to_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        }

        if not self.company_id:
            raise UserError("Branch is required!\nPlease select branch first.")  
        
        if self.company_id:
            body['dealerId'] = self._resolve_dealer_id()
        
        if self.id_spk:
            body['idSPK'] = self.id_spk
        
        if self.id_prospect:
            body['idProspect'] = self.id_prospect
        
        return body
    
    def _add_process_log(self, message, log_type='INFO'):
        """
        Add message to process_log field
        
        Args:
            message: Message to log
            log_type: Type of log (INFO, WARNING, ERROR, SUCCESS)
        """
        self.ensure_one()
        current_log = self.process_log or ""
        prefix = f"[{log_type}]" if log_type else ""
        new_log = f"{prefix} {message}" if prefix else message
        
        if current_log:
            self.process_log = current_log + "\n" + new_log
        else:
            self.process_log = new_log

    def _build_success_log(self, endpoint, item, record):
        """Build standard success log per DGI transaction."""
        self.ensure_one()
        identifier = self._get_item_identifier(endpoint, item)
        detail_lines = self._get_success_log_lines(endpoint, item, record)
        return "\n".join([identifier] + detail_lines)

    def _get_success_log_lines(self, endpoint, item, record):
        """Return detail lines for the standard success log.
        Child wizards can inject additional lines via record.with_context(dgi_success_log_lines=['Line 1', 'Line 2'])."""
        self.ensure_one()
        rec_name = record.display_name or getattr(record, "name", False) or f"ID:{record.id}"
        lines = [f"- Record: {rec_name}"]
        
        extra_logs = record.env.context.get("dgi_success_log_lines", [])
        if isinstance(extra_logs, list):
            for log in extra_logs:
                # Ensure the line has the standard dash prefix
                if not log.startswith("-"):
                    log = f"- {log}"
                lines.append(log)
                
        return lines

    def _normalize_parse_response_hook_result(self, hook_result):
        """Normalize parse hook result into a structured dict."""
        if isinstance(hook_result, dict):
            return {
                "proceed": bool(hook_result.get("proceed", False)),
                "message": hook_result.get("message"),
                "log_type": hook_result.get("log_type", "WARNING"),
            }
        if isinstance(hook_result, str):
            return {
                "proceed": False,
                "message": hook_result,
                "log_type": "WARNING",
            }
        return {
            "proceed": bool(hook_result),
            "message": False,
            "log_type": "WARNING",
        }
    
    def action_call_dgi_api(self, endpoint_code, auto_parse=True, target_model=None):
        """Generic method to call DGI API with optional auto-parsing
        
        Args:
            endpoint_code: Code of endpoint configuration (e.g., 'doch_proses_stnk')
            auto_parse: If True and endpoint has response mappings, auto-parse with engine
            target_model: Target model for parsing (optional, uses mapping if not specified)
            
        Returns:
            If auto_parse=True and mappings exist: list of parsed/created records
            Otherwise: dict of raw API response
        """
        self.ensure_one()
        
        # Get API config from branch setting
        api_config = self._get_api_config()
        
        # Get endpoint configuration
        endpoint = api_config.endpoint_config_ids.filtered(
            lambda e: e.code == endpoint_code
        )
        
        if not endpoint:
            raise UserError(
                f"Endpoint '{endpoint_code}' not found!\n"
                f"Please configure endpoint in API Configuration."
            )
        
        # Build request body
        request_body = self._prepare_api_request_body()
        
        # Call API
        response = api_config.action_call_endpoint(
            endpoint=endpoint,
            params=request_body,
            raise_exception=False 
        )
        
        
        # Auto-parse if enabled and mappings or template configured
        if auto_parse and (endpoint.response_mapping_ids or endpoint.output_template):
            # Check for API Error - handle different response formats
            # Format 1: {'status': 400, 'title': '...', 'errors': {...}}
            # Format 2: {'http_status_code': 403, 'message': '...'}
            # Format 3: {'error': 'Unauthorized...', 'error_description': '...'}
            # Format 4: {'status': 0, 'message': '{...json string...}'}
            
            is_error = False
            error_msg = ""
            status_code = response.get('status') or response.get('http_status_code')
            
            if isinstance(response, dict):
                # Standard HTTP Errors
                if isinstance(status_code, int) and status_code >= 400:
                    is_error = True
                    error_title = response.get('title') or response.get('message', 'API Error')
                    errors = response.get('errors', {})
                    error_msg = f"HTTP {status_code}: {error_title} - {errors}" if errors else f"HTTP {status_code}: {error_title}"
                # Application Error format (status = 0)
                elif str(response.get('status')) == '0':
                    is_error = True
                    raw_msg = response.get('message', 'Unknown Error')
                    # Sometime message is a JSON string
                    try:
                        msg_json = json.loads(raw_msg)
                        if isinstance(msg_json, dict):
                            error_msg = f"{msg_json.get('status', 'Error')}: {msg_json.get('message', raw_msg)}"
                        else:
                            error_msg = raw_msg
                    except (json.JSONDecodeError, TypeError):
                        error_msg = raw_msg
                # OAuth/Gateway Error format
                elif 'error' in response:
                    is_error = True
                    error_msg = f"{response.get('error')}: {response.get('error_description', '')}"

            if is_error:
                # Log error but return empty list to avoid crash
                self._add_process_log(f"API Error: {error_msg}", 'ERROR')
                return []

            # Get response data
            data = response.get('data', [])
            
            if not data:
                return []
            
            # Use DGI engine to parse - returns dict or list of dicts
            engine = self.env['tw.dgi.engine']
            
            # Handle different response structures
            if isinstance(data, list):
                # Data is a list - process each item separately
                all_values = []
                logs = []
                
                for item in data:
                    try:
                        with self.env.cr.savepoint():
                            # Hook for custom validation/modification before parsing
                            parse_hook_result = self._normalize_parse_response_hook_result(
                                self._prepare_parse_response(endpoint, item)
                            )
                            if not parse_hook_result["proceed"]:
                                if parse_hook_result["message"]:
                                    logs.append(
                                        f"[{parse_hook_result['log_type']}] {parse_hook_result['message']}"
                                    )
                                continue
                                
                            # Engine auto-detects array fields within each item
                            parsed = engine.parse_response(
                                endpoint=endpoint,
                                response_json=item,
                                target_model=target_model
                            )

                            # Skip None results (filtered records)
                            if parsed is None:
                                continue
                            
                            # Collect results (could be single dict or list of dicts)
                            items_to_process = []
                            if isinstance(parsed, list):
                                items_to_process.extend(parsed)
                            elif isinstance(parsed, dict):
                                items_to_process.append(parsed)
                            
                            # Create records if target model is configured
                            if endpoint.target_model_id:
                                for vals in items_to_process:
                                    # Extract special keys (starting with _) untuk context
                                    context_vals = {
                                        k: vals.pop(k) for k in list(vals.keys())
                                        if isinstance(k, str) and k.startswith('_')
                                    }
                                    # Wrap each record in its own savepoint so that:
                                    # - A failed create/compute raises rollback only for this item
                                    # - [SUCCESS] is only appended AFTER full success (no rollback)
                                    # - [ERROR] is appended and [SUCCESS] is never added on failure
                                    try:
                                        with self.env.cr.savepoint():
                                            record = self.with_context(**context_vals)._create_record_from_response(endpoint, vals)
                                            # Flush to trigger any pending computes/constraints
                                            # (e.g. @api.depends that raise UserError/ValidationError)
                                            # so exceptions surface here (inside savepoint), not outside.
                                            self.env.flush_all()
                                        # Only reach here if savepoint committed without error
                                        all_values.append(record)
                                        if record and len(record) > 0 and record.id:
                                            logs.append(f"[SUCCESS] {self._build_success_log(endpoint, item, record)}")
                                    except Exception as item_err:
                                        identifier = self._get_item_identifier(endpoint, item)
                                        error_msg = f"Error processing {identifier}: {str(item_err)}"
                                        logs.append(f"[ERROR] {error_msg}")
                                        _logger.error(
                                            f"DGI Sync Error on item {identifier}: {str(item_err)}\n"
                                            f"Full Item Data: {str(item)}"
                                        )

                            else:
                                # Just return values if no target model
                                all_values.extend(items_to_process)
                            
                    except Exception as e:
                        # Capture error but continue processing other items
                        identifier = self._get_item_identifier(endpoint, item)
                        error_msg = f"Error processing {identifier}: {str(e)}"
                        logs.append(f"[ERROR] {error_msg}")
                        _logger.error(f"DGI Sync Error on item {identifier}: {str(e)}\nFull Item Data: {str(item)}")
                
                
                # Update log field with all messages
                for log in logs:
                    # Extract log type from message
                    if log.startswith('[SUCCESS]'):
                        self._add_process_log(log.replace('[SUCCESS] ', ''), 'SUCCESS')
                    elif log.startswith('[ERROR]'):
                        self._add_process_log(log.replace('[ERROR] ', ''), 'ERROR')
                    elif log.startswith('[WARNING]'):
                        self._add_process_log(log.replace('[WARNING] ', ''), 'WARNING')
                    elif log.startswith('[INFO]'):
                        self._add_process_log(log.replace('[INFO] ', ''), 'INFO')
                    else:
                        self._add_process_log(log, 'INFO')
                
                return all_values
            else:
                # Data is single object - engine handles array detection
                parsed = engine.parse_response(
                    endpoint=endpoint,
                    response_json=data,
                    target_model=target_model
                )
                
                # Return as list for consistency
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    return [parsed]
                else:
                    return []
        
        # Return raw response if auto_parse disabled or no mappings
        return response
    
    def action_sync_dgi_data(self, endpoint_code):
        """
        Generic method to sync data from DGI API with complete flow:
        - Call API
        - Parse response
        - Create records
        - Update wizard
        - Show notification
        
        Args:
            endpoint_code: Code of endpoint configuration (e.g., 'doch_proses_stnk')
            
        Returns:
            dict: Odoo action (notification)
        """
        self.ensure_one()
        
        try:
            # Always clear previous wizard result so each sync shows a clean per-run log.
            self.write({
                'process_log': False,
                'found_count': 0,
            })
            
            # Call API (parsing + creation + logging handled inside)
            response = self.action_call_dgi_api(endpoint_code)
            # Validate response
            data = []
            if isinstance(response, list):
                data = response
            elif isinstance(response, dict):
                if response.get('status') != 1:
                    error_msg = response.get('error', 'Unknown error')
                    raise UserError(f"API Error: {error_msg}")
                data = response.get('data', [])
            else:
                raise UserError(f"Invalid API response format: {type(response)}")
            # Check if no data
            if not data:
                has_process_feedback = bool(
                    self.process_log and (
                        '[ERROR]' in self.process_log
                        or '[WARNING]' in self.process_log
                        or '[SUCCESS]' in self.process_log
                        or '[INFO]' in self.process_log
                    )
                )
                if not has_process_feedback:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'No Data',
                            'message': 'No data found from DGI for the selected period',
                            'type': 'warning',
                            'sticky': False,
                        }
                    }
            
            # Update wizard
            processed_count = len(data) if isinstance(data, list) else 0
            self.write({'found_count': processed_count})
            
            # Generate detailed message from process_log
            log_content = self.process_log or ""
            success_lines = [line for line in log_content.split('\n') if '[SUCCESS]' in line]
            error_lines = [line for line in log_content.split('\n') if '[ERROR]' in line]
            warning_lines = [line for line in log_content.split('\n') if '[WARNING]' in line]
            
            success_count = len(success_lines)
            # Count both ERROR and WARNING as failures for notification
            error_count = len(error_lines) + len(warning_lines)
            
            # Build message
            message_parts = []
            if success_count > 0:
                # Extract record names from success logs
                record_names = []
                for line in success_lines[:5]:  # Show max 5 records
                    if 'Created' in line:
                        name = line.split('Created')[-1].strip()
                        record_names.append(name)
                
                message_parts.append(f"✓ {success_count} record(s) created successfully")
                if record_names:
                    message_parts.append(f"  → {', '.join(record_names)}")
                    if success_count > 5:
                        message_parts.append(f"  → ... and {success_count - 5} more")
            
            if error_count > 0:
                message_parts.append(f"✗ {error_count} record(s) skipped/failed")
                message_parts.append("  → Check Process Log for details")
            
            message = '\n'.join(message_parts)
            
            # Determine notification type
            if error_count > 0 and success_count == 0:
                notif_type = 'danger'
                title = 'DGI Sync Failed'
            elif error_count > 0:
                notif_type = 'warning'
                title = 'DGI Sync Completed with Errors'
            else:
                notif_type = 'success'
                title = 'DGI Sync Successful'
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': title,
                    'message': message,
                    'type': notif_type,
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_window',
                        'res_model': self._name,
                        'res_id': self.id,
                        'view_mode': 'form',
                        'views': [[False, 'form']],
                        'target': 'new',
                        'context': self.env.context,
                    }
                }
            }
            
        except Exception as e:
            raise UserError(f"Error syncing DGI data: {str(e)}")
    

    def _prepare_parse_response(self, endpoint, response_item):
        """
        Hook method to validate or modify response item before parsing.
        Override this method in specific wizards to implement custom business logic.
        
        Args:
            endpoint: tw.endpoint.configuration record
            response_item: dict of single data item from API response
            
        Returns:
            bool: True to proceed with parsing, False to skip this item
            
        Raises:
            UserError/ValidationError: If validation fails and should stop process
        """
        return True

    def _get_item_identifier(self, endpoint, item):
        """
        Hook method to extract a readable identifier from the raw JSON item for logging.
        Override this method in specific wizards so you don't hardcode keys in the engine.
        
        Args:
            endpoint: tw.endpoint.configuration record
            item: dict of raw JSON item
        
        Returns:
            str: Identifier (e.g., '15537-SLU-2600085') or 'Item'
        """
        return item.get('id') or 'Item'

    def _prepare_record_value(self, endpoint, values):
        """
        Hook method to prepare values before record creation.
        Override this method in specific wizards to implement custom business logic.
        
        Args:
            endpoint: tw.endpoint.configuration record
            values: dict of values for creation
            
        Returns:
            dict: Prepared values for record creation
        """
        values.update({
            'is_dgi': True,
            'dgi_get_date': fields.Datetime.now(),
            'dgi_get_uid': self.env.user.id
        })

        return values

    def _create_record_from_response(self, endpoint, values):
        """
        Create Odoo record from parsed values.
        Can be overridden for custom creation logic.
        
        Args:
            endpoint: tw.endpoint.configuration record
            values: dict of values for creation
            
        Returns:
            Created record
        """
        values = self._prepare_record_value(endpoint, values)
        target_model_name = endpoint.target_model_id.model
        return self.env[target_model_name].sudo().create(values)

    def _create_log_error_dgi(self, name, url, method, description, doch):
        method = self.env['tw.selection'].search([
            ('name', '=', method),
            ('type','=','ApiMethod')
        ], limit=1)
        self.env['tw.api.log'].sudo().create_api_log(
            name,
            url,
            description,
            ip_address=False,
            response=False,
            payload=False,
            header=False,
            response_code=False,
            status_code=False,
            reference=False,
            transaction_id=False,
            api_type_id=False,
            method_id=method.id if method else False,
            model_id=False
        )

    def _resolve_dealer_id(self):
        """Resolve the dealerId value for DGI API request body.

        Reads dealer_id_source from the branch's DGI API configuration
        to determine which field on res.company to use as the DGI dealer ID.

        Source options (configured on tw.api.configuration):
            - 'atpm_code'        : company_id.atpm_code (default)
            - 'code'             : company_id.code
            - 'parent_atpm_code' : company_id.parent_id.atpm_code
                                   (for ASP branches that use their Main Dealer's DGI code)

        Falls back to atpm_code if api_config is unavailable.

        Returns:
            str: Resolved dealer ID value.
        """
        self.ensure_one()
        company = self.company_id

        try:
            api_config = self._get_api_config()
            source = api_config.dealer_id_source or "atpm_code"
        except Exception:
            # Graceful fallback: if api_config not available, use atpm_code
            source = "atpm_code"

        if source == "code":
            return company.code
        elif source == "parent_atpm_code":
            parent = company.parent_id
            if not parent:
                _logger.warning(
                    "dealer_id_source is 'parent_atpm_code' but branch '%s' has no parent company. "
                    "Falling back to atpm_code.",
                    company.name,
                )
                return company.atpm_code
            return parent.atpm_code
        else:
            # Default: atpm_code
            return company.atpm_code
