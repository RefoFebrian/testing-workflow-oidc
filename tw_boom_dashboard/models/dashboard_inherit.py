from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression
import logging
import sys
_logger = logging.getLogger(__name__)

class DashboardAccessLine(models.Model):
    _name = "dashboard.access.line"
    _description = 'Dashboard Access Group Domain'

    dashboard_id = fields.Many2one('dashboard.dashboard', string='Dashboard', ondelete='cascade')
    group_id = fields.Many2one('res.groups', string='Access Group', required=True)
    domain = fields.Char(string='Domain', help="Domain format: [('field', 'operator', value)]")


class Dashboard(models.Model):
    _inherit = "dashboard.dashboard"
    
    @api.model
    def _register_hook(self):
        """
        Called when module is loaded. This runs on both INSTALL and UPGRADE.
        Use this to import new dashboards that were added during upgrade.
        """
        super()._register_hook()
        
        # Import dashboards if there are new empty ones or if we want to sync
        # self.env.registry._init is True during module install/update
        if self.env.registry._init:
            try:
                from ..hooks import import_dashboard_json
                # Pass force=True to allow syncing JSON changes to existing dashboards
                import_dashboard_json(self.env, force=True)
            except Exception as e:
                _logger.warning("TW BOOM Dashboard: Error in _register_hook: %s", str(e))

    header_domain = fields.Char(string='Global Domain', help="Base domain to apply to all charts in this dashboard.")
    access_line_ids = fields.One2many('dashboard.access.line', 'dashboard_id', string='Access Group Domains')
    evaluated_header_domain = fields.Json(string='Evaluated Header Domain', compute='_compute_evaluated_header_domain', store=False)
    
    @api.depends('header_domain', 'access_line_ids', 'access_line_ids.domain')
    def _compute_evaluated_header_domain(self):
        """Compute and cache the evaluated header domain for use in auto-reload."""
        for record in self:
            record.evaluated_header_domain = record.get_computed_header_domain()

    def get_computed_header_domain(self):
        """
        Evaluate and combine header_domain with access group domains.
        """
        self.ensure_one()
        combined_domain = []
        
        # 1. Base Header Domain
        if self.header_domain:
            # We use a dummy chart record to access evaluate_odoo_domain
            dummy_chart = self.env['dashboard.chart'].sudo()
            base_eval = dummy_chart.evaluate_odoo_domain(self.header_domain)
            if base_eval:
                combined_domain = base_eval
        
        # 2. Access Group Line Domains
        user_groups = self.env.user.groups_id
        for line in self.access_line_ids:
            if line.group_id in user_groups and line.domain:
                dummy_chart = self.env['dashboard.chart'].sudo()
                line_eval = dummy_chart.evaluate_odoo_domain(line.domain)
                if line_eval:
                    if combined_domain:
                        combined_domain = expression.AND([combined_domain, line_eval])
                    else:
                        combined_domain = line_eval
                    
        return combined_domain

    def write(self, vals):
        """
        Override to tag layout dimensions as 36-column grid when saved.
        """
        if 'grid_stack_dimensions' in vals and isinstance(vals['grid_stack_dimensions'], list):
            for item in vals['grid_stack_dimensions']:
                if isinstance(item, dict):
                    item['is_36_col'] = True
        return super(Dashboard, self).write(vals)

    def get_charts_details(self):
        """
        Override to adjust dimensions for custom chart types and scale to 36-column grid.
        Also injects Header Domain into context for dynamic filtering.
        """
        # Use the computed field value (works for both initial load and auto-reload)
        header_domain = self.evaluated_header_domain or []
        if header_domain:
            self = self.with_context(header_domain=header_domain)
            
        result = super(Dashboard, self).get_charts_details()
        
        # New Grid Constants
        NEW_COLS = 36
        OLD_COLS = 12
        COL_SCALE = NEW_COLS // OLD_COLS # 3
        
        # Assuming original cell height was 90 and new is 30
        ROW_SCALE = 3 

        if result and len(result) > 1 and isinstance(result[1], list):
            chart_data_list = result[1]
            grid_stack = self.grid_stack_dimensions or []
            
            # Check if this record has already been transitioned to 36-col grid.
            # We check the actual field on the model, not the data returned by super.
            # Heuristic: if any width in the DB is > 12, it's definitely 36-col.
            # Flag: if 'is_36_col' is present in any item in the DB, it's 36-col.
            already_scaled = any(
                item.get('is_36_col') or (item.get('w') or 0) > OLD_COLS 
                for item in grid_stack
            )
            
            for chart_data in chart_data_list:
                c_type = chart_data.get('chart_type')
                
                if not already_scaled:
                    chart_data['x'] = (chart_data.get('x') or 0) * COL_SCALE
                    chart_data['w'] = (chart_data.get('w') or 6) * COL_SCALE
                    chart_data['y'] = (chart_data.get('y') or 0) * ROW_SCALE
                    chart_data['h'] = (chart_data.get('h') or 4) * ROW_SCALE
                
                if c_type in ['greeting', 'quote', 'birthday', 'label', 'progress_bar', 'filter']:
                    chart_data['minh'] = 1
                    if c_type == 'birthday':
                        chart_data['minh'] = 1
                
                # Fetch color_palette, header_font_size, header_font_color, font_weight_bold,
                # header_font_weight, header_font_style, and font_style from DB for each chart
                # Note: result[1] contains records data. We can optimize this if needed, 
                # but for now, we just want to bridge the data.
                chart_rec = self.env['dashboard.chart'].browse(int(chart_data.get('id')))
                if chart_rec.exists():
                    chart_data['color_palette'] = chart_rec.color_palette
                    chart_data['header_font_size'] = chart_rec.header_font_size
                    chart_data['header_font_color'] = chart_rec.header_font_color
                    chart_data['font_weight_bold'] = chart_rec.font_weight_bold
                    chart_data['chart_orientation'] = chart_rec.chart_orientation or 'vertical'
                    chart_data['show_legend'] = chart_rec.show_legend
                    
        return result

    def find_next_position(self, items, new_width, grid_columns=36):
        """
        Override to use 36 columns by default.
        """
        return super(Dashboard, self).find_next_position(items, new_width, grid_columns=grid_columns)

    def dashboard_export_json(self):
        """
        Override to include custom fields in list_measure_ids export.
        """
        charts_list = super(Dashboard, self).dashboard_export_json()
        
        # Create a map of charts by name for reliable matching
        charts_by_name = {c['name']: c for c in charts_list}
        
        for chart in self.chart_ids:
            chart_dict = charts_by_name.get(chart.name)
            if chart_dict:
                # Relation fields (Many2one names)
                chart_dict.update({
                    'chart_user_field': chart.chart_user_field_id.name if chart.chart_user_field_id else False,
                    'font_family': chart.font_family_id.name if chart.font_family_id else False,
                    'header_font_family': chart.header_font_family_id.name if chart.header_font_family_id else False,
                    'filter_field': chart.filter_field_id.name if chart.filter_field_id else False,
                    'filter_model': chart.filter_model_id.model if chart.filter_model_id else False,
                    'filter_date_field': chart.filter_date_field_id.name if chart.filter_date_field_id else False,
                    'progress_value_field': chart.progress_value_field_id.name if chart.progress_value_field_id else False,
                    'progress_target_field': chart.progress_target_field_id.name if chart.progress_target_field_id else False,
                })

                # One2many: filter_mapping_ids
                chart_dict['filter_mapping_ids'] = [
                    {
                        'filter_type': m.filter_type,
                        'target_field': m.target_field_id.name if m.target_field_id else False,
                        'filter_technical_name': m.filter_technical_name,
                    }
                    for m in chart.filter_mapping_ids
                ]

                # One2many: stacked_segment_ids
                chart_dict['stacked_segment_ids'] = [
                    {
                        'sequence': s.sequence,
                        'name': s.name,
                        'color': s.color,
                        'domain': s.domain,
                    }
                    for s in chart.stacked_segment_ids
                ]

                # Override list_measure_ids to include custom fields
                chart_dict['list_measure_ids'] = [
                    {
                        'sequence': m.sequence,
                        'list_field_id': m.list_field_id.name,
                        'list_measure_id': m.list_measure_id.name,
                        'value_type': m.value_type,
                        'model_id': m.model_id.model,
                        'field_id': m.field_id.name,
                        # Custom fields from tw_boom_dashboard
                        'label_name': m.label_name,
                        'measure_domain': m.measure_domain,
                        'measure_color': m.measure_color,
                    }
                    for m in chart.list_measure_ids
                ]

                # Add list_field_ids with custom fields
                chart_dict['list_field_ids'] = [
                    {
                        'sequence': m.sequence,
                        'list_field_id': m.list_field_id.name,
                        'list_measure_id': m.list_measure_id.name,
                        'value_type': m.value_type,
                        'model_id': m.model_id.model,
                        'field_id': m.field_id.name,
                        # Custom fields from tw_boom_dashboard
                        'label_name': m.label_name,
                        'measure_domain': m.measure_domain,
                        'measure_color': m.measure_color,
                    }
                    for m in chart.list_field_ids
                ]

                # Basic fields
                chart_dict.update({
                    'kpi_data1_color': chart.kpi_data1_color,
                    'kpi_data2_color': chart.kpi_data2_color,
                    'kpi_label1': chart.kpi_label1,
                    'kpi_label2': chart.kpi_label2,
                    'header_font_size': chart.header_font_size,
                    'header_font_color': chart.header_font_color,
                    'header_font_weight': chart.header_font_weight,
                    'header_font_style': chart.header_font_style,
                    'font_weight_bold': chart.font_weight_bold,
                    'font_style': chart.font_style,
                    'color_palette': chart.color_palette,
                    'content_source': chart.content_source,
                    'custom_content': chart.custom_content,
                    'custom_author': chart.custom_author,
                    'is_user_filter': chart.is_user_filter,
                    'progress_source_type': chart.progress_source_type,
                    'progress_value_domain': chart.progress_value_domain,
                    'progress_target_domain': chart.progress_target_domain,
                    'progress_value_query': chart.progress_value_query,
                    'progress_target_query': chart.progress_target_query,
                    'progress_target_manual': chart.progress_target_manual,
                    'progress_color': chart.progress_color,
                    'progress_bg_color': chart.progress_bg_color,
                    'progress_label_format': chart.progress_label_format,
                    'progress_show_label': chart.progress_show_label,
                    'filter_type': chart.filter_type,
                    'filter_label': chart.filter_label,
                    'filter_placeholder': chart.filter_placeholder,
                    'filter_technical_name': chart.filter_technical_name,
                    'filter_domain': chart.filter_domain,
                    'filter_date_start_default': chart.filter_date_start_default,
                    'filter_date_end_default': chart.filter_date_end_default,
                    'smart_filter_area': chart.smart_filter_area,
                    'smart_filter_branch': chart.smart_filter_branch,
                    'stacked_show_legend': chart.stacked_show_legend,
                    'stacked_show_percentage': chart.stacked_show_percentage,
                    'chart_orientation': chart.chart_orientation,
                    'show_legend': chart.show_legend,
                })
        
        return charts_list

    def dashboard_import_json(self, json_payload_wrapped):
        """
        Override to handle custom fields in list_measure_ids import and support intelligent sync.
        """
        is_sync = json_payload_wrapped.get('is_sync', False)
        force = json_payload_wrapped.get('force', False)
        json_payload = json_payload_wrapped.get('json_payload', [])
        
        # Map of charts in JSON by name for easy lookup
        json_charts_map = {p.get('name'): p for p in json_payload if p.get('name')}
        
        # If syncing, we need to separate existing charts from new ones
        new_json_payload = []
        updated_chart_ids = []
        
        if is_sync:
            # Find all existing charts for this dashboard
            existing_charts = self.env['dashboard.chart'].sudo().search([('dashboard_id', '=', self.id)])
            existing_charts_by_name = {c.name: c for c in existing_charts}
            for chart_name, payload in json_charts_map.items():
                existing_chart = existing_charts_by_name.get(chart_name)
                if not (existing_chart and (existing_chart.is_managed or force)):
                    new_json_payload.append(payload)

            # If no new charts, we don't need to call super().dashboard_import_json with a full payload

            if not new_json_payload:
                # We still need to run the enrichment logic for updated_chart_ids
                result = {'type': 'success', 'message': 'Existing charts updated'}
            else:
                # Only pass the NEW charts to the parent import
                result = super(Dashboard, self).dashboard_import_json({'json_payload': new_json_payload})
        else:
            # Standard import behavior (full replace or append)
            result = super(Dashboard, self).dashboard_import_json({'json_payload': json_payload})
        
        if result.get('type') == 'success':
            # Use sudo search to ensure we find newly created charts for this dashboard
            # This is more reliable than self.chart_ids if the O2M is not yet updated in the session
            all_charts = self.env['dashboard.chart'].sudo().search([('dashboard_id', '=', self.id)])
            
            # If we are syncing, we only care about the charts that were in the JSON
            # This includes both the ones we updated and the ones the parent just created
            target_charts = all_charts.filtered(lambda c: c.name in json_charts_map)
            
            # Get current grid stack to merge layout changes
            current_grid_stack = self.grid_stack_dimensions or []
            grid_map = {item.get('chartId'): item for item in current_grid_stack if item.get('chartId')}
            
            for chart in target_charts:
                custom_data = json_charts_map.get(chart.name)
                if custom_data:
                    # 1. Layout Sync
                    if custom_data.get('chart_position'):
                        pos = custom_data['chart_position']
                        grid_item = grid_map.get(chart.id)
                        if grid_item:
                            grid_item.update({
                                'x': pos.get('x', grid_item.get('x')),
                                'y': pos.get('y', grid_item.get('y')),
                                'w': pos.get('w', grid_item.get('w')),
                                'h': pos.get('h', grid_item.get('h')),
                                'is_36_col': True
                            })
                        else:
                            current_grid_stack.append({
                                'chartId': chart.id,
                                'x': pos.get('x', 0),
                                'y': pos.get('y', 0),
                                'w': pos.get('w', 6),
                                'h': pos.get('h', 4),
                                'is_36_col': True
                            })
                    
                    # 2. Metadata & Field Sync
                    chart_vals = {'is_managed': True}

                    if not chart.technical_name:
                        # Auto-generate technical name for future syncs if missing
                        chart_vals['technical_name'] = chart.name.lower().replace(' ', '_')

                    # Many2one fields lookup (sudo search by name/model)
                    if custom_data.get('chart_user_field'):
                        f_rec = self.env['ir.model.fields'].sudo().search([
                            ('model_id', '=', chart.model_id.id),
                            ('name', '=', custom_data['chart_user_field'])
                        ], limit=1)
                        if f_rec:
                            chart_vals['chart_user_field_id'] = f_rec.id

                    if custom_data.get('font_family'):
                        font_rec = self.env['tw.dashboard.font'].sudo().search([('name', '=', custom_data['font_family'])], limit=1)
                        if font_rec:
                            chart_vals['font_family_id'] = font_rec.id

                    if custom_data.get('header_font_family'):
                        font_rec = self.env['tw.dashboard.font'].sudo().search([('name', '=', custom_data['header_font_family'])], limit=1)
                        if font_rec:
                            chart_vals['header_font_family_id'] = font_rec.id

                    if custom_data.get('filter_field'):
                        f_rec = self.env['ir.model.fields'].sudo().search([
                            ('model_id', '=', chart.model_id.id),
                            ('name', '=', custom_data['filter_field'])
                        ], limit=1)
                        if f_rec:
                            chart_vals['filter_field_id'] = f_rec.id

                    if custom_data.get('filter_model'):
                        m_rec = self.env['ir.model'].sudo().search([('model', '=', custom_data['filter_model'])], limit=1)
                        if m_rec:
                            chart_vals['filter_model_id'] = m_rec.id

                    if custom_data.get('filter_date_field'):
                        f_rec = self.env['ir.model.fields'].sudo().search([
                            ('model_id', '=', chart.model_id.id),
                            ('name', '=', custom_data['filter_date_field'])
                        ], limit=1)
                        if f_rec:
                            chart_vals['filter_date_field_id'] = f_rec.id

                    if custom_data.get('progress_value_field'):
                        f_rec = self.env['ir.model.fields'].sudo().search([
                            ('model_id', '=', chart.model_id.id),
                            ('name', '=', custom_data['progress_value_field'])
                        ], limit=1)
                        if f_rec:
                            chart_vals['progress_value_field_id'] = f_rec.id

                    if custom_data.get('progress_target_field'):
                        f_rec = self.env['ir.model.fields'].sudo().search([
                            ('model_id', '=', chart.model_id.id),
                            ('name', '=', custom_data['progress_target_field'])
                        ], limit=1)
                        if f_rec:
                            chart_vals['progress_target_field_id'] = f_rec.id

                    # Regular fields
                    field_keys = [
                        'kpi_data1_color', 'kpi_data2_color', 'kpi_label1', 'kpi_label2',
                        'header_font_size', 'header_font_color', 'header_font_weight', 'header_font_style',
                        'font_weight_bold', 'font_style', 'color_palette', 'content_source',
                        'custom_content', 'custom_author', 'is_user_filter', 'progress_source_type',
                        'progress_value_domain', 'progress_target_domain', 'progress_value_query',
                        'progress_target_query', 'progress_target_manual', 'progress_color',
                        'progress_bg_color', 'progress_label_format', 'progress_show_label',
                        'filter_type', 'filter_label', 'filter_placeholder', 
                        'filter_technical_name', 'filter_domain',
                        'filter_date_start_default', 'filter_date_end_default',
                        'smart_filter_area', 'smart_filter_branch', 'stacked_show_legend', 
                        'stacked_show_percentage', 'chart_orientation', 'show_legend'
                    ]
                    for key in field_keys:
                        if key in custom_data:
                            chart_vals[key] = custom_data[key]
                    
                    if chart_vals:
                        chart.write(chart_vals)
                    
                    # Update One2many: filter_mapping_ids (Intelligent Sync)
                    if custom_data.get('filter_mapping_ids'):
                        existing_mappings = chart.filter_mapping_ids
                        mappings_to_keep = self.env['dashboard.chart.filter.mapping'].sudo()
                        
                        for m_data in custom_data['filter_mapping_ids']:
                            f_rec = self.env['ir.model.fields'].sudo().search([
                                ('model_id', '=', chart.model_id.id),
                                ('name', '=', m_data.get('target_field'))
                            ], limit=1)
                            
                            if f_rec:
                                # Try to find matching existing mapping (Robust comparison)
                                match = existing_mappings.filtered(lambda m:
                                    (m.filter_type or '') == (m_data.get('filter_type') or '') and 
                                    m.target_field_id.id == f_rec.id and 
                                    (m.filter_technical_name or '') == (m_data.get('filter_technical_name') or '')
                                )
                                
                                if match:
                                    mappings_to_keep |= match[0]
                                else:
                                    # Create new if no match
                                    chart.write({'filter_mapping_ids': [(0, 0, {
                                        'filter_type': m_data.get('filter_type'),
                                        'target_field_id': f_rec.id,
                                        'filter_technical_name': m_data.get('filter_technical_name')
                                    })]})
                        
                        # Only unlink those that are no longer in JSON
                        (existing_mappings - mappings_to_keep).unlink()

                    # Update One2many: stacked_segment_ids (Intelligent Sync)
                    if custom_data.get('stacked_segment_ids'):
                        existing_segments = chart.stacked_segment_ids
                        segments_to_keep = self.env['dashboard.chart.stacked.segment'].sudo()
                        
                        for s_data in custom_data['stacked_segment_ids']:
                            # Match by name as unique identifier (Robust comparison)
                            match = existing_segments.filtered(lambda s: (s.name or '') == (s_data.get('name') or ''))

                            vals = {
                                'sequence': s_data.get('sequence', 10),
                                'color': s_data.get('color'),
                                'domain': s_data.get('domain'),
                            }
                            
                            if match:
                                match[0].write(vals)
                                segments_to_keep |= match[0]
                            else:
                                vals['name'] = s_data.get('name')
                                chart.write({'stacked_segment_ids': [(0, 0, vals)]})
                                
                        # Only unlink those that are no longer in JSON
                        (existing_segments - segments_to_keep).unlink()

                    # Update list_measure_ids with custom fields
                    list_measures_data = custom_data.get('list_measure_ids', [])
                    for measure in chart.list_measure_ids:
                        for lm_data in list_measures_data:
                            if (lm_data.get('sequence') == measure.sequence
                                    and lm_data.get('list_measure_id') == (measure.list_measure_id.name or lm_data.get('list_measure_id'))):
                                measure_vals = {}
                                for k in ['label_name', 'measure_domain', 'measure_color']:
                                    if lm_data.get(k):
                                        measure_vals[k] = lm_data[k]
                                if measure_vals:
                                    measure.write(measure_vals)
                                break

                    # Update list_field_ids with custom fields
                    list_fields_data = custom_data.get('list_field_ids', [])
                    for field in chart.list_field_ids:
                        for lf_data in list_fields_data:
                            if (lf_data.get('sequence') == field.sequence
                                    and lf_data.get('list_field_id') == (field.list_field_id.name or lf_data.get('list_field_id'))):
                                field_vals = {}
                                for k in ['label_name', 'measure_domain', 'measure_color']:
                                    if lf_data.get(k):
                                        field_vals[k] = lf_data[k]
                                if field_vals:
                                    field.write(field_vals)
                                break
            
            # Save the final merged layout
            self.sudo().write({'grid_stack_dimensions': current_grid_stack})
        
        return result
    