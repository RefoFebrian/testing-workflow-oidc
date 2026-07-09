from odoo import models, fields, api
from odoo.tools import groupby
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from types import SimpleNamespace

CASCADE_SELECTION = {
    'greeting': 'cascade', 
    'quote': 'cascade', 
    'birthday': 'cascade', 
    'label': 'cascade',
    'progress_bar': 'cascade',
    'filter': 'cascade',
    'stacked_progress': 'cascade',
}

class DashboardChart(models.Model):
    _inherit = "dashboard.chart"

    chart_type = fields.Selection(selection_add=[
        ('greeting', 'Greeting'),
        ('quote', 'Quote'),
        ('birthday', 'Birthday'),
        ('label', 'Label'),
        ('progress_bar', 'Progress Bar'),
        ('filter', 'Filter'),
        ('stacked_progress', 'Stacked Progress Bar'),
        ],
        ondelete=CASCADE_SELECTION   # Required when extending selection
    )

    content_source = fields.Selection(
        [("dynamic", "Dynamic"), ("manual", "Manual")],
        string="Content Source",
        default="dynamic",
    )
    custom_content = fields.Text(string="Custom Content")
    custom_author = fields.Char(string="Quote Author")
    color_palette = fields.Text(string="Color Palette", help="Comma separated hex colors, e.g. #FF4560, #775DD0, #00E396")

    # Header Styling
    header_font_size = fields.Integer(string="Header Font Size", default=22)
    header_font_color = fields.Char(string="Header Font Color")
    header_font_weight = fields.Integer(
        string='Header Font Weight',
        default=700,
        help='CSS font-weight value (100-900). Normal=400, Bold=700'
    )
    header_font_style = fields.Selection([
        ('normal', 'Normal'),
        ('italic', 'Italic')
    ], string='Header Font Style', default='normal')
    font_style = fields.Selection([
        ('normal', 'Normal'),
        ('italic', 'Italic')
    ], string='Chart Font Style', default='normal')
    font_weight_bold = fields.Integer(
        string='Chart Font Weight',
        default=700,
        help='CSS font-weight value (100-900). Normal=400, Bold=700'
    )
    
    # Chart Orientation for Stacked Charts
    chart_orientation = fields.Selection(
        [("vertical", "Vertical"), ("horizontal", "Horizontal")],
        string="Chart Orientation",
        default="vertical",
        help="Select the orientation for bar/column charts. Vertical shows columns, Horizontal shows bars."
    )
    
    # Chart Legend Configuration
    show_legend = fields.Boolean(
        string="Show Legend",
        default=False,
        help="Display a legend on the chart showing the series names."
    )
    
    # User Filter Configuration
    is_user_filter = fields.Boolean(
        string="Filter by Current User",
        default=False,
        help="Enable to filter chart data based on the current logged-in user."
    )
    chart_user_field_id = fields.Many2one(
        "ir.model.fields",
        string="User Field",
        domain="[('model_id', '=', model_id), ('ttype', '=', 'many2one'), ('relation', 'in', ['res.users', 'hr.employee'])]",
        help="Select the field that links records to users (e.g., user_id, create_uid, employee_id)."
    )
    
    font_family_id = fields.Many2one("tw.dashboard.font", string="Chart Font Family")
    header_font_family_id = fields.Many2one("tw.dashboard.font", string="Header Font Family")
    
    company_id = fields.Many2one("res.company", string="Branch", required=False)
    is_managed = fields.Boolean(string="Managed by System", default=False, help="If true, this chart is managed by the system JSON config and will be updated during sync.")
    technical_name = fields.Char(string="Technical Name", help="Unique identifier for dashboard sync.")


    # =============================================
    # KPI Chart Color Configuration
    # =============================================
    kpi_data1_color = fields.Char(
        string="Data 1 Color",
        default="#333333",
        help="Color for the first/main data value in KPI chart"
    )
    kpi_data2_color = fields.Char(
        string="Data 2 Color", 
        default="#888888",
        help="Color for the second/comparison data value in KPI chart"
    )
    
    # Layout 6 Selection Extension
    layout_type = fields.Selection(
        selection_add=[('layout6', 'Layout 6 (with Custom Label)')],
        ondelete={'layout6': 'set default'}
    )
    
    # KPI Custom Labels for Layout 6 (separate labels for Data 1 and Data 2)
    kpi_label1 = fields.Char(
        string="Data 1 Label",
        help="Label for Data 1 (shown at bottom left). Example: 'Open'"
    )
    kpi_label2 = fields.Char(
        string="Data 2 Label",
        help="Label for Data 2 (shown at bottom right). Example: 'Overdue'"
    )

    # =============================================
    # Progress Bar Chart Fields
    # =============================================
    progress_source_type = fields.Selection([
        ('field', 'By Field'),
        ('domain', 'By Domain (Count)'),
        ('query', 'By SQL Query'),
    ], string="Progress Source Type", default="field",
       help="How to get progress value: Field (sum field values), Domain (count records), Query (raw SQL)")
    
    # Field-based source
    progress_value_field_id = fields.Many2one(
        "ir.model.fields", 
        string="Progress Value Field",
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['integer', 'float', 'monetary'])]",
        help="Field to use as progress value (current)"
    )
    progress_target_field_id = fields.Many2one(
        "ir.model.fields",
        string="Progress Target Field", 
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['integer', 'float', 'monetary'])]",
        help="Field to use as target value (100%)"
    )
    
    # Domain-based source
    progress_value_domain = fields.Text(
        string="Progress Value Domain",
        help="Domain to count records as progress value. Example: [('state', '=', 'done')]"
    )
    progress_target_domain = fields.Text(
        string="Target Value Domain",
        help="Domain to count records as target. Example: [('state', 'in', ['draft', 'confirm', 'done'])]"
    )
    
    # Query-based source
    progress_value_query = fields.Text(
        string="Progress Value Query",
        help="SQL query returning single numeric value. Use %(uid)s for current user ID. Example: SELECT COUNT(*) FROM tw_boom_task WHERE state = 'done' AND user_id = %(uid)s"
    )
    progress_target_query = fields.Text(
        string="Target Value Query", 
        help="SQL query returning single numeric value for target. Example: SELECT COUNT(*) FROM tw_boom_task WHERE user_id = %(uid)s"
    )
    
    progress_target_manual = fields.Float(string="Manual Target Value", help="Use this if target is a fixed value instead of field/domain/query")
    progress_color = fields.Char(string="Progress Bar Color", default="#4CAF50")
    progress_bg_color = fields.Char(string="Progress Background Color", default="#e0e0e0")
    progress_label_format = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('value', 'Value Only'),
        ('value_target', 'Value / Target'),
    ], string="Progress Label Format", default="percentage")
    progress_show_label = fields.Boolean(string="Show Progress Label", default=True)
    
    # Preview/Test fields (computed)
    progress_preview_value = fields.Char(
        string="Preview: Value Result",
        compute="_compute_progress_preview",
        store=False
    )
    progress_preview_target = fields.Char(
        string="Preview: Target Result",
        compute="_compute_progress_preview",
        store=False
    )
    progress_preview_percentage = fields.Char(
        string="Preview: Percentage",
        compute="_compute_progress_preview",
        store=False
    )

    # =============================================
    # Stacked Progress Bar Fields
    # =============================================
    stacked_segment_ids = fields.One2many(
        'dashboard.chart.stacked.segment',
        'chart_id',
        string="Progress Segments",
        help="Define the segments/colors for the stacked progress bar"
    )
    smart_filter_area = fields.Boolean(
        string="Auto-Filter by User Area",
        default=False,
        help="Automatically filter data by user.area_id.company_ids"
    )
    smart_filter_branch = fields.Boolean(
        string="Auto-Filter by User Companies",
        default=False,
        help="Automatically filter data by user.company_ids"
    )
    stacked_show_legend = fields.Boolean(
        string="Show Legend",
        default=True,
        help="Display a legend above the progress bar"
    )
    stacked_show_percentage = fields.Boolean(
        string="Show Percentage in Bar",
        default=True,
        help="Display percentage text inside each segment"
    )

    # =============================================
    # Filter Layout Fields
    # =============================================
    filter_type = fields.Selection([
        ('employee', 'Employee'),
        ('date_range', 'Date Range'),
        ('many2one', 'Many2One Field'),
        ('selection', 'Selection Field'),
        ('manual', 'Manual Input'),
    ], string="Filter Type", default="employee")
    filter_field_id = fields.Many2one(
        "ir.model.fields",
        string="Filter Field",
        help="Field to filter on (for many2one/selection filter types)"
    )
    filter_model_id = fields.Many2one(
        "ir.model",
        string="Filter Source Model",
        help="Model to get filter options from"
    )
    filter_label = fields.Char(string="Filter Label", help="Custom label for the filter")
    filter_placeholder = fields.Char(string="Filter Placeholder", default="Select...")
    filter_date_field_id = fields.Many2one(
        "ir.model.fields",
        string="Date Field to Filter",
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]",
        help="Date field that will be filtered by the date range"
    )
    filter_domain = fields.Char(string="Filter Domain", help="Domain to filter the dropdown options for Many2One filters. E.g. [('company_type', '=', 'company')]")
    filter_technical_name = fields.Char(
        string="Filter Technical Name",
        help="Unique identifier for this filter (e.g. area_manager, spv, admin_manager). "
             "Used as the key in dashboard state to allow multiple filters of the same type."
    )
    filter_date_start_default = fields.Char(
        string="Date Start Default",
        help="Python expression or date string (YYYY-MM-DD) for default start date. "
             "Shortcuts: start_last_month, start_this_month, today. "
             "Example: start_last_month"
    )
    filter_date_end_default = fields.Char(
        string="Date End Default",
        help="Python expression or date string (YYYY-MM-DD) for default end date. "
             "Shortcuts: end_last_month, end_this_month, today. "
             "Example: end_last_month"
    )
    
    filter_backend_model_id = fields.Many2one(
        'ir.model', 
        string="Backend Model for Filter", 
        compute='_compute_filter_backend_model_id',
        store=False
    )

    @api.depends('filter_type', 'filter_model_id', 'model_id')
    def _compute_filter_backend_model_id(self):
        """
        Compute the model to be used for filtering fields.
        - For 'many2one', use the explicitly selected filter_model_id.
        - For 'selection', use the chart's main model_id.
        """
        for rec in self:
            if rec.filter_type == 'many2one':
                rec.filter_backend_model_id = rec.filter_model_id
            elif rec.filter_type == 'selection':
                rec.filter_backend_model_id = rec.model_id
            else:
                rec.filter_backend_model_id = False

    # =============================================
    # Dashboard Filter Mapping
    # =============================================
    filter_mapping_ids = fields.One2many(
        'dashboard.chart.filter.mapping',
        'chart_id',
        string="Filter Mappings",
        help="Define which dashboard filters affect this chart and which field they target"
    )


    def evaluate_odoo_domain(self, domain_string):
        """
        Override to inject dynamic variables (user, context, uid) and merge with Header Domain.
        """
        # Reproduce base logic with expanded context
        class OdooSafeDatetime:
            def __init__(self, dt):
                self._dt = dt
            def to_utc(self):
                if hasattr(self._dt, "replace") and self._dt.tzinfo is None:
                    utc_dt = self._dt
                else:
                    utc_dt = fields.Datetime.to_datetime(self._dt)
                return OdooSafeDatetime(utc_dt)
            def strftime(self, fmt):
                return self._dt.strftime(fmt)

        class OdooDatetimeClass:
            @staticmethod
            def combine(date_obj, time_obj):
                combined = datetime.combine(date_obj, time_obj)
                return OdooSafeDatetime(combined)

        class DatetimeModule:
            datetime = OdooDatetimeClass
            time = time

        def get_context_today():
            return fields.Datetime.context_timestamp(self, datetime.now()).date()

        # Dynamic date variables
        today = fields.Datetime.context_timestamp(self, datetime.now()).date()
        start_today = datetime.combine(today, time.min)
        end_today = datetime.combine(today, time.max)
        
        # Week boundaries (Monday to Sunday)
        start_week = datetime.combine(today - timedelta(days=today.weekday()), time.min)
        end_week = datetime.combine(today + timedelta(days=6 - today.weekday()), time.max)
        
        # Month boundaries
        start_month = datetime.combine(today.replace(day=1), time.min)
        if today.month == 12:
            end_month = datetime.combine(today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1), time.max)
        else:
            end_month = datetime.combine(today.replace(month=today.month+1, day=1) - timedelta(days=1), time.max)

        eval_context = {
            "datetime": DatetimeModule(),
            "context_today": get_context_today,
            "relativedelta": relativedelta,
            "user": self.env.user,
            "context": self.env.context,
            "uid": self.env.uid,
            "company_ids": self.env.user.company_ids.ids if self.env.user.company_ids else [self.env.company.id],
            # Dynamic date variables
            "today": today,
            "start_today": start_today,
            "end_today": end_today,
            "start_week": start_week,
            "end_week": end_week,
            "start_month": start_month,
            "end_month": end_month,
        }

        try:
            res = safe_eval(domain_string, eval_context)
        except Exception as e:
            res = []

        # =============================================
        # APPLY DASHBOARD FILTER MAPPINGS FROM CONTEXT
        # =============================================
        dashboard_filters = self.env.context.get('dashboard_filters')
        if dashboard_filters:
            # Determine target model for mapping validation
            if self.env.context.get('evaluating_kpi'):
                target_model = self.kpi_model_id.model if self.kpi_model_id else self.model_id.model
            else:
                target_model = self.model_id.model
            
            res = self._apply_dashboard_filter_mappings(res, dashboard_filters, target_model)

        # Merge with Header Domain if present in context
        header_domain = self.env.context.get('header_domain')
        if header_domain:
            if res:
                try:
                    return expression.AND([header_domain, res])
                except Exception as e:
                    return res
            else:
                return header_domain
        return res

    @api.depends('progress_source_type', 'model_id', 'domain',
                 'progress_value_field_id', 'progress_target_field_id',
                 'progress_value_domain', 'progress_target_domain',
                 'progress_value_query', 'progress_target_query',
                 'progress_target_manual')
    def _compute_progress_preview(self):
        """Compute preview values for domain/query testing"""
        for rec in self:
            progress_value = 0
            target_value = rec.progress_target_manual or 100
            error_msg = ""
            
            if rec.chart_type != 'progress_bar':
                rec.progress_preview_value = ""
                rec.progress_preview_target = ""
                rec.progress_preview_percentage = ""
                continue
                
            source_type = rec.progress_source_type or 'field'
            
            try:
                # ========== BY FIELD (Sum) ==========
                if source_type == 'field' and rec.model_id and rec.progress_value_field_id:
                    model_obj = rec.env[rec.model_id.model]
                    domain = rec.evaluate_odoo_domain(rec.domain) if rec.domain else []
                    records = model_obj.sudo().search(domain)
                    if records:
                        field_name = rec.progress_value_field_id.name
                        progress_value = sum(getattr(r, field_name) or 0 for r in records)
                        
                        if rec.progress_target_field_id:
                            target_field_name = rec.progress_target_field_id.name
                            target_value = sum(getattr(r, target_field_name) or 0 for r in records) or target_value
                
                # ========== BY DOMAIN (Count) ==========
                elif source_type == 'domain' and rec.model_id:
                    model_obj = rec.env[rec.model_id.model].sudo()
                    
                    # Get base domain from chart's global domain
                    base_domain = rec.evaluate_odoo_domain(rec.domain) if rec.domain else []
                    
                    if rec.progress_value_domain:
                        value_domain = rec.evaluate_odoo_domain(rec.progress_value_domain)
                        # Merge with base domain
                        if base_domain:
                            value_domain = expression.AND([base_domain, value_domain])
                        progress_value = model_obj.search_count(value_domain)
                    
                    if rec.progress_target_domain:
                        target_domain = rec.evaluate_odoo_domain(rec.progress_target_domain)
                        # Merge with base domain
                        if base_domain:
                            target_domain = expression.AND([base_domain, target_domain])
                        target_value = model_obj.search_count(target_domain) or target_value
                
                # ========== BY QUERY (Raw SQL) ==========
                elif source_type == 'query':
                    params = {'uid': rec.env.uid}
                    
                    if rec.progress_value_query:
                        rec.env.cr.execute(rec.progress_value_query, params)
                        result = rec.env.cr.fetchone()
                        progress_value = result[0] if result else 0
                    
                    if rec.progress_target_query:
                        rec.env.cr.execute(rec.progress_target_query, params)
                        result = rec.env.cr.fetchone()
                        target_value = result[0] if result else target_value
                        
            except Exception as e:
                error_msg = str(e)
            
            # Calculate percentage
            percentage = (progress_value / target_value * 100) if target_value > 0 else 0
            percentage = min(percentage, 100)
            
            if error_msg:
                rec.progress_preview_value = f"Error: {error_msg}"
                rec.progress_preview_target = ""
                rec.progress_preview_percentage = ""
            else:
                rec.progress_preview_value = f"{progress_value:,.0f}"
                rec.progress_preview_target = f"{target_value:,.0f}"
                rec.progress_preview_percentage = f"{percentage:.1f}%"

    def _init_configuration(self):
        """
        Override to add custom fields to the configuration namespace.
        """
        conf, domain = super(DashboardChart, self)._init_configuration()
        # Add legend and user filter configuration
        conf.show_legend = self.show_legend
        conf.is_user_filter = self.is_user_filter
        conf.chart_user_field = self.chart_user_field_id.name if self.chart_user_field_id else False
        return conf, domain

    # =============================================
    # Area Expansion Technical Names
    # =============================================
    AREA_EXPANSION_TECH_NAMES = ('area_manager', 'spv', 'admin_manager', 'area')

    def _apply_dashboard_filter_mappings(self, domain, dashboard_filters, model_name=None):
        """
        Helper to apply dashboard filter mappings to a given domain.
        Ensures fields exist on the target model to prevent crashes.
        Supports Area Expansion for specific technical names.
        """
        if not dashboard_filters or not self.filter_mapping_ids:
            return domain
            
        model_name = model_name or self.model_id.model
        model_obj = self.env.get(model_name)
        if model_obj is None:
            return domain

        for mapping in self.filter_mapping_ids:
            filter_type = mapping.filter_type
            tech_name = mapping.filter_technical_name
            target_field = mapping.target_field_id.name if mapping.target_field_id else None
            
            if not target_field or target_field not in model_obj._fields:
                continue
            
            # Use technical name as lookup key if present, otherwise fall back to filter_type
            lookup_key = tech_name or filter_type
            filter_value = dashboard_filters.get(lookup_key)
            if filter_value is None and filter_type != 'date_range':
                continue

            if filter_type == 'date_range':
                date_start = dashboard_filters.get('date_start')
                date_end = dashboard_filters.get('date_end')
                if date_start:
                    domain = expression.AND([domain, [(target_field, '>=', date_start)]])
                if date_end:
                    domain = expression.AND([domain, [(target_field, '<=', date_end)]])
            elif tech_name and tech_name in self.AREA_EXPANSION_TECH_NAMES:
                # =============================================
                # AREA EXPANSION LOGIC
                # Instead of simple equality, expand to all
                # employees & branches within the selected
                # employee's area.
                # =============================================
                domain = self._apply_area_expansion_filter(
                    domain, filter_value, target_field, model_obj, tech_name=tech_name
                )
            elif filter_type in ('employee', 'many2one'):
                try:
                    val = int(filter_value)
                    domain = expression.AND([domain, [(target_field, '=', val)]])
                except (ValueError, TypeError):
                    pass
            elif filter_type == 'selection':
                domain = expression.AND([domain, [(target_field, '=', filter_value)]])
            elif filter_type == 'manual':
                domain = expression.AND([domain, [(target_field, 'ilike', filter_value)]])
        
        return domain

    def _apply_area_expansion_filter(self, domain, filter_value, target_field, model_obj, tech_name=None):
        """
        Expand filter to all employees/branches within a selected area.
        Supports two modes:
          - tech_name='area': filter_value is a res.area ID
          - Otherwise: filter_value is an hr.employee ID, area is resolved from employee
        """
        try:
            record_id = int(filter_value)
        except (ValueError, TypeError):
            return domain

        # =============================================
        # MODE 1: Direct Area Filter (res.area ID)
        # =============================================
        if tech_name == 'area':
            area = self.env['res.area'].sudo().browse(record_id)
            if not area.exists():
                return domain
            branch_ids = area.company_ids.ids
            if not branch_ids:
                return domain
        else:
            # =============================================
            # MODE 2: Manager -> Area/User -> Branches
            # Derive branches from the employee's area
            # and user multi-company access.
            # =============================================
            employee = self.env['hr.employee'].sudo().browse(record_id)
            if not employee.exists():
                return domain

            # Collect branches from area and user access
            branch_ids = []
            if hasattr(employee, 'area_id') and employee.area_id:
                branch_ids += employee.area_id.company_ids.ids
            if employee.user_id and employee.user_id.company_ids:
                branch_ids += employee.user_id.company_ids.ids
            if employee.company_id:
                branch_ids.append(employee.company_id.id)

            # Deduplicate
            branch_ids = list(set(branch_ids))

            if not branch_ids:
                # Fallback: filter by single employee if no branch info found
                return expression.AND([domain, [(target_field, '=', record_id)]])

        # Get all active employees in those branches
        employees_in_area = self.env['hr.employee'].sudo().search([
            ('company_id', 'in', branch_ids),
            ('working_end_date', '=', False),
            ('active', '=', True),
        ])
        emp_ids = employees_in_area.ids or [record_id]

        # Build the expanded domain
        # Prefer company_id filter if available, otherwise use employee_id
        has_company = 'company_id' in model_obj._fields
        has_employee = target_field in model_obj._fields

        if has_company and has_employee:
            area_domain = ['|',
                (target_field, 'in', emp_ids),
                ('company_id', 'in', branch_ids),
            ]
        elif has_company:
            area_domain = [('company_id', 'in', branch_ids)]
        else:
            area_domain = [(target_field, 'in', emp_ids)]

        return expression.AND([domain, area_domain])

    def _process_domain(self, domain, extra_action, group_by_id):
        """
        Override to apply user-based filtering when is_user_filter is enabled.
        Also apply dashboard filter mappings from extra_action.
        """
        # SAFE CALL: Only call super if group_by_id is present or if no drill-down domain in extra_action
        # This prevents crash in base module which tries to access group_by_id.name
        if group_by_id or not (extra_action and extra_action.get("domain")):
            domain = super(DashboardChart, self)._process_domain(domain, extra_action, group_by_id)
        
        # Apply user filter if enabled and a user field is selected
        if self.is_user_filter and self.chart_user_field_id:
            user_field_name = self.chart_user_field_id.name
            # Get the relation model to determine how to filter
            if self.chart_user_field_id.relation == 'res.users':
                domain = expression.AND([domain, [(user_field_name, '=', self.env.uid)]])
            elif self.chart_user_field_id.relation == 'hr.employee':
                # If field relates to hr.employee, find employees linked to current user
                current_employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
                if current_employee:
                    domain = expression.AND([domain, [(user_field_name, '=', current_employee.id)]])
        
        # =============================================
        # APPLY DASHBOARD FILTER MAPPINGS
        # =============================================
        dashboard_filters = extra_action.get('dashboard_filters', {}) if extra_action else {}
        if dashboard_filters and self.filter_mapping_ids:
            domain = self._apply_dashboard_filter_mappings(domain, dashboard_filters)
        
        return domain


    def get_list_view_data(self, conf_obj):
        """
        Override to support 'count' value_type and 'sub_group_by' in grouped list views.
        Also handles crashes in the base method when non-numeric fields are used as measures.
        """
        if conf_obj.list_type != 'grouped':
            return super(DashboardChart, self).get_list_view_data(conf_obj)

        # For grouped list views, we handle everything here to avoid crashes in the base method
        # and to support our custom features (count, selection labels, domain filtering).
        ir_model_fields_obj = self.env["ir.model.fields"].sudo()
        record_obj = self.env[conf_obj.model]
        measure_ids = conf_obj.list_measure_ids
        
        # Build columns list for the result (mirroring base module structure)
        columns = []
        group_by_field = ir_model_fields_obj.search([("name", "=", conf_obj.group_by), ("model", "=", conf_obj.model)], limit=1)
        if group_by_field:
            columns.append({"id": "group_by", "column_name": group_by_field.name, "name": group_by_field.field_description})
        
        for i, m in enumerate(measure_ids):
            # m is a dictionary from _init_configuration override or _handle_dirty_data
            col_rec = ir_model_fields_obj.browse(m['list_measure_id'])
            
            # Use measure ID to make column key unique (handling same field multiple times)
            # Fallback to index if 'id' is missing (e.g. during dirty/preview with unsaved records)
            unique_id = m.get('id') or f"new_{i}"
            unique_col_key = f"{col_rec.name}_{unique_id}"
            
            # Use custom label if provided, else field description
            if m.get('label_name'):
                label = m['label_name']
            else:
                label = col_rec.field_description
                if m.get('measure_domain'):
                    label += f" ({m['measure_domain']})"

            columns.append({
                "id": unique_id, 
                "column_name": unique_col_key, 
                "name": label, 
                "value_type": m['value_type'],
                "color": m.get('measure_color') or '#000000'
            })

        # Fetch and sort records
        sort_order = "ASC" if conf_obj.sort_order == "ascending" else "DESC"
        domain = conf_obj.domain or []
        # Support company filter if applicable (from user's recent edit)
        if conf_obj.company and "company_id" in record_obj._fields:
            domain.append(("company_id", "in", [conf_obj.company, False]))

        records = record_obj.sudo().search(
            domain, 
            order=f"{conf_obj.sort_field} {sort_order}" if conf_obj.sort_field else None
        )

        def format_val(record, field_name, time_range):
            if not field_name: return ''
            value = getattr(record, field_name)
            field = record._fields[field_name]
            
            if field.type in ['date', 'datetime'] and time_range and value:
                # Basic formatting (can be extended)
                if time_range == "day": return value.strftime("%d %B %Y")
                elif time_range == "week": return f"Week {value.isocalendar()[1]} {value.year}"
                elif time_range == "month": return value.strftime("%B %Y")
                elif time_range == "quarter": return f"Q{(value.month - 1) // 3 + 1} {value.year}"
                elif time_range == "year": return value.strftime("%Y")
            elif field.type == 'selection' and value:
                return dict(field._description_selection(self.env)).get(value, value)
            elif isinstance(value, models.Model):
                return value.display_name or ''
            return value or ''

        def get_group_key(record):
            return format_val(record, conf_obj.group_by, getattr(conf_obj, 'time_range', False))

        grouped_by_records = groupby(records, key=get_group_key)
        
        new_record_list = []
        group_by_field_name = conf_obj.group_by
        
        for group_label, grouped_records in grouped_by_records:
            grouped_records = list(grouped_records)
            record_set = {"id": group_label, group_by_field_name: group_label}
            
            for i, m in enumerate(measure_ids):
                col_name = ir_model_fields_obj.browse(m['list_measure_id']).name
                unique_id = m.get('id') or f"new_{i}"
                unique_col_key = f"{col_name}_{unique_id}"
                val_type = m['value_type']
                measure_domain = m.get('measure_domain')
                
                # Filter records based on domain if provided
                target_records = grouped_records
                if measure_domain:
                    try:
                        domain = safe_eval(measure_domain)
                        # We need to filter the specific records in this group
                        # Create a recordset from the list to use filtered_domain
                        group_recordset = record_obj.browse([r.id for r in grouped_records])
                        filtered_recs = group_recordset.filtered_domain(domain)
                        target_records = list(filtered_recs)
                    except Exception:
                        pass # Ignore invalid domains to prevent crashes

                # Robust calculation: only sum if field is numeric
                if val_type == 'count':
                    record_set[unique_col_key] = len(target_records)
                else:
                    field_type = records._fields[col_name].type
                    is_numeric = field_type in ['integer', 'float', 'monetary']
                    
                    if val_type == 'sum':
                        record_set[unique_col_key] = sum(getattr(r, col_name) or 0 for r in target_records) if is_numeric else 0
                    elif val_type == 'average':
                        vals = [getattr(r, col_name) or 0 for r in target_records] if is_numeric else []
                        record_set[unique_col_key] = round(sum(vals) / len(vals), 2) if vals else 0
            
            record_set["currentIds"] = [r.id for r in grouped_records]
            new_record_list.append(record_set)
        
        # Apply record limit
        return {
            "columns": columns, 
            "records": new_record_list,
            "name": conf_obj.name,
            "model": conf_obj.model,
        }

    def get_chart_data(self, chart_type, name, **kwargs):
        """
        Override to handle greeting, quote, and birthday chart types.
        Also uses sudo() for Global Dashboards to avoid multi-company AccessErrors
        when charts span across companies.
        Also injects header_domain context for auto-reload filtering persistence.
        """
        # Inject header_domain context for auto-reload scenarios
        current_header_domain = self.dashboard_id.evaluated_header_domain or []
        
        # Merge with employee filter from extra_action (kwargs)
        extra_action = kwargs.get('extra_action', {})
        if extra_action and extra_action.get('employee_id'):
            emp_id = int(extra_action['employee_id'])
            
            # Smart filtering: Check if model supports employee_id
            emp_domain = []
            model_cls = self.env.get(self.model)
            if model_cls is not None and ('employee_id' in model_cls._fields or 'user_id' in model_cls._fields):
                # Prefer direct employee_id
                if 'employee_id' in model_cls._fields:
                    emp_domain = [('employee_id', '=', emp_id)]
                elif 'user_id' in model_cls._fields:
                    emp_domain = [('user_id.employee_ids', 'in', [emp_id])]
            
            # If we differ on KPI model, ensure compatibility or skip to avoid crash
            if emp_domain and self.kpi_model:
                kpi_cls = self.env.get(self.kpi_model)
                # If KPI model is different and lacks employee field, standard header_domain would crash it.
                # But evaluate_odoo_domain merges header_domain BLINDLY for all domains.
                # So we must only add if SAFE for ALL models used in this chart.
                if kpi_cls and not ('employee_id' in kpi_cls._fields or 'user_id' in kpi_cls._fields):
                    emp_domain = [] # Unsafe to apply globally
            
            if emp_domain:
                if current_header_domain:
                    current_header_domain = expression.AND([current_header_domain, emp_domain])
                else:
                    current_header_domain = emp_domain

        if current_header_domain:
            self = self.with_context(header_domain=current_header_domain)
        
        # Inject dashboard_filters into context if present (even if empty to support reset)
        if extra_action and 'dashboard_filters' in extra_action:
            self = self.with_context(dashboard_filters=extra_action['dashboard_filters'])

        # Use sudo if the parent dashboard is global (no company assigned)
        if not self.dashboard_id.company_id:
            self = self.sudo()

        # Call super (it will use the sudo environment if the record was sudoed above)
        res = super(DashboardChart, self).get_chart_data(chart_type, name, **kwargs)
        
        # Inject color_palette if present
        # Inject custom fields if result is a dict
        dirty_data = kwargs.get('data', {}) if kwargs.get('isDirty') else {}
        if isinstance(res, dict):
            # Check for dirty data first to support Live Preview
            
            res['color_palette'] = dirty_data.get('color_palette') or self.color_palette
            res['header_font_size'] = dirty_data.get('header_font_size') or self.header_font_size
            res['header_font_color'] = dirty_data.get('header_font_color') or self.header_font_color
            res['header_font_weight'] = dirty_data.get('header_font_weight') or self.header_font_weight
            res['header_font_style'] = dirty_data.get('header_font_style') or self.header_font_style
            res['font_weight_bold'] = dirty_data.get('font_weight_bold') or self.font_weight_bold
            res['font_style'] = dirty_data.get('font_style') or self.font_style
            
            # Handle Many2one for font families
            font_id = self._normalize_m2o(dirty_data.get('font_family_id')) or self.font_family_id.id
            header_font_id = self._normalize_m2o(dirty_data.get('header_font_family_id')) or self.header_font_family_id.id
            
            res['font_family'] = self.env['tw.dashboard.font'].browse(font_id).font_family_css if font_id else 'Arial'
            res['header_font_family'] = self.env['tw.dashboard.font'].browse(header_font_id).font_family_css if header_font_id else 'Arial'
            
            # Keep original IDs for form view persistence during preview
            res['font_family_id'] = font_id
            res['header_font_family_id'] = header_font_id
            
            # KPI Data Colors
            res['kpi_data1_color'] = dirty_data.get('kpi_data1_color') or self.kpi_data1_color or '#333333'
            res['kpi_data2_color'] = dirty_data.get('kpi_data2_color') or self.kpi_data2_color or '#888888'
            
            # KPI Custom Labels (for Layout 6)
            res['kpi_label1'] = dirty_data.get('kpi_label1') or self.kpi_label1 or ''
            res['kpi_label2'] = dirty_data.get('kpi_label2') or self.kpi_label2 or ''

        if chart_type in ['greeting', 'quote', 'birthday', 'label']:
            data = {
                'id': str(self.id),
                'name': self.name,
                'chart_type': chart_type,
                'content_source': self.content_source,
                'custom_content': self.custom_content,
                'custom_author': self.custom_author,
                'theme': self.theme,
                'background_color': self.background_color,
                'font_size': self.font_size,
                'font_color': self.font_color,
                'font_weight': self.font_weight, # Old field, keep for compatibility
                'font_weight_bold': self.font_weight_bold, # New field
                'font_style': self.font_style, # New field
                'font_family': self.font_family_id.font_family_css or 'Arial',
                'header_font_family': self.header_font_family_id.font_family_css or 'Arial',
                'text_align': self.text_align,
                'color_palette': self.color_palette,
            }
            
            # Label type is purely static content from custom_content
            if chart_type == 'label':
                data['label_text'] = self.custom_content or ""
            
            # Add dynamic data if needed
            elif chart_type == 'greeting' and self.content_source == 'dynamic':
                welcome_data = self.env['tw.boom.task'].action_welcome_text()
                welcome_data = welcome_data.get('data', [])
                if len(welcome_data) >= 2:
                    data['dynamic_content'] = f"{welcome_data[0].get('greet', '')}, {welcome_data[0].get('name', '')}"
            
            elif chart_type == 'quote' and self.content_source == 'dynamic':
                quote_data = self.env['tw.boom.task'].get_quote_only()
                data['dynamic_content'] = quote_data.get('quote', '')
                data['dynamic_author'] = quote_data.get('author', '')

            # Birthday doesn't need extra dynamic data fetch here, handled by frontend or separate RPC if needed.
            # But we might want to check if it's the user's birthday to show a badge/highlight.
            elif chart_type == 'birthday':
                # Optional: fetch birthday status if needed for initial render state
                birthday_data = self.env['tw.boom.task'].get_birthdays_only()
                data['is_birthday'] = birthday_data.get('birthday', False)
                data['birthday_message'] = birthday_data.get('message', '')

            return data

        # =============================================
        # Progress Bar Chart Data
        # =============================================
        if chart_type == 'progress_bar':
            # Get styling from dirty_data (preview) or from saved record
            progress_color = dirty_data.get('progress_color') or self.progress_color or '#4CAF50'
            progress_bg_color = dirty_data.get('progress_bg_color') or self.progress_bg_color or '#e0e0e0'
            progress_label_format = dirty_data.get('progress_label_format') or self.progress_label_format or 'percentage'
            progress_show_label = dirty_data.get('progress_show_label') if 'progress_show_label' in dirty_data else self.progress_show_label
            
            data = {
                'id': str(self.id),
                'name': self.name,
                'chart_type': chart_type,
                'background_color': dirty_data.get('background_color') or self.background_color,
                'progress_color': progress_color,
                'progress_bg_color': progress_bg_color,
                'progress_label_format': progress_label_format,
                'progress_show_label': progress_show_label if progress_show_label is not None else True,
                'font_size': dirty_data.get('font_size') or self.font_size,
                'font_color': dirty_data.get('font_color') or self.font_color,
                'font_weight': dirty_data.get('font_weight_bold') or self.font_weight_bold or self.font_weight or 'normal',
                'font_style': dirty_data.get('font_style') or self.font_style or 'normal',
                'font_family': self.font_family_id.font_family_css or 'Arial',
            }
            
            progress_value = 0
            target_value = self.progress_target_manual or 100
            source_type = self.progress_source_type or 'field'
            
            try:
                # ========== BY FIELD (Sum) ==========
                if source_type == 'field' and self.model_id and self.progress_value_field_id:
                    model_obj = self.env[self.model_id.model]
                    domain = self.evaluate_odoo_domain(self.domain) if self.domain else []
                    
                    # Apply dashboard filters
                    domain = self._process_domain(domain, extra_action, False)
                    
                    records = model_obj.sudo().search(domain)
                    if records:
                        field_name = self.progress_value_field_id.name
                        progress_value = sum(getattr(r, field_name) or 0 for r in records)
                        
                        if self.progress_target_field_id:
                            target_field_name = self.progress_target_field_id.name
                            target_value = sum(getattr(r, target_field_name) or 0 for r in records) or target_value
                
                # ========== BY DOMAIN (Count) ==========
                elif source_type == 'domain' and self.model_id:
                    model_obj = self.env[self.model_id.model].sudo()
                    
                    # Get base domain from chart's global domain
                    base_domain = self.evaluate_odoo_domain(self.domain) if self.domain else []
                    
                    # Apply dashboard filters to base domain
                    base_domain = self._process_domain(base_domain, extra_action, False)
                    
                    # Progress value = count of records matching value domain
                    if self.progress_value_domain:
                        value_domain = self.evaluate_odoo_domain(self.progress_value_domain)
                        # Merge with base domain
                        if base_domain:
                            value_domain = expression.AND([base_domain, value_domain])
                        progress_value = model_obj.search_count(value_domain)
                    
                    # Target value = count of records matching target domain
                    if self.progress_target_domain:
                        target_domain = self.evaluate_odoo_domain(self.progress_target_domain)
                        # Merge with base domain
                        if base_domain:
                            target_domain = expression.AND([base_domain, target_domain])
                        target_value = model_obj.search_count(target_domain) or target_value
                
                # ========== BY QUERY (Raw SQL) ==========
                elif source_type == 'query':
                    params = {'uid': self.env.uid}
                    
                    if self.progress_value_query:
                        self.env.cr.execute(self.progress_value_query, params)
                        result = self.env.cr.fetchone()
                        progress_value = result[0] if result else 0
                    
                    if self.progress_target_query:
                        self.env.cr.execute(self.progress_target_query, params)
                        result = self.env.cr.fetchone()
                        target_value = result[0] if result else target_value
                        
            except Exception as e:
                pass
            
            # Calculate percentage
            percentage = (progress_value / target_value * 100) if target_value > 0 else 0
            percentage = min(percentage, 100)  # Cap at 100%
            
            data['progress_value'] = progress_value
            data['target_value'] = target_value
            data['percentage'] = round(percentage, 1)
            
            return data

        # =============================================
        # Filter Layout Data
        # =============================================
        if chart_type == 'filter':
            data = {
                'id': str(self.id),
                'name': self.name,
                'chart_type': chart_type,
                'background_color': self.background_color,
                'filter_type': self.filter_type or 'employee',
                'filter_technical_name': self.filter_technical_name or '',
                'filter_label': self.filter_label or self._get_default_filter_label(),
                'filter_placeholder': self.filter_placeholder or 'Select...',
                'font_size': self.font_size,
                'font_color': self.font_color,
                'font_family': self.font_family_id.font_family_css or 'Arial',
            }
            
            # Get filter options based on type
            if self.filter_type == 'employee':
                data['filter_options'] = self._get_employee_options()
            elif self.filter_type == 'many2one' and self.filter_model_id:
                data['filter_options'] = self._get_many2one_options()
            elif self.filter_type == 'selection' and self.filter_field_id:
                data['filter_options'] = self._get_selection_options()
            elif self.filter_type == 'date_range':
                data['date_field'] = self.filter_date_field_id.name if self.filter_date_field_id else None
                # Evaluate default date expressions
                if self.filter_date_start_default:
                    data['filter_date_start_default'] = self._evaluate_date_expression(self.filter_date_start_default)
                if self.filter_date_end_default:
                    data['filter_date_end_default'] = self._evaluate_date_expression(self.filter_date_end_default)
            else:
                data['filter_options'] = []
            
            return data

        # =============================================
        # Stacked Progress Bar Data
        # =============================================
        if chart_type == 'stacked_progress':
            data = {
                'id': str(self.id),
                'name': self.name,
                'chart_type': chart_type,
                'background_color': dirty_data.get('background_color') or self.background_color,
                'font_size': dirty_data.get('font_size') or self.font_size,
                'font_color': dirty_data.get('font_color') or self.font_color,
                'font_weight': dirty_data.get('font_weight_bold') or self.font_weight_bold or self.font_weight or 'normal',
                'font_style': dirty_data.get('font_style') or self.font_style or 'normal',
                'font_family': self.font_family_id.font_family_css or 'Arial',
                'show_legend': dirty_data.get('stacked_show_legend') if 'stacked_show_legend' in dirty_data else self.stacked_show_legend,
                'show_percentage': dirty_data.get('stacked_show_percentage') if 'stacked_show_percentage' in dirty_data else self.stacked_show_percentage,
                'is_grouped': False,
                'groups': [],
                'segments': [],
                'total': 0,
                'model': self.model_id.model if self.model_id else '',
            }
            
            if not self.model_id:
                return data
            
            try:
                model_obj = self.env[self.model_id.model].sudo()
                
                # Build Smart Filter domain
                smart_domain = []
                if self.smart_filter_area:
                    user = self.env.user
                    if hasattr(user, 'area_id') and user.area_id:
                        area_company_ids = user.area_id.company_ids.ids
                        if area_company_ids:
                            smart_domain.append(('company_id', 'in', area_company_ids))
                elif self.smart_filter_branch:
                    user_company_ids = self.env.user.company_ids.ids
                    if user_company_ids:
                        smart_domain.append(('company_id', 'in', user_company_ids))
                
                # Base domain from chart configuration
                base_domain = self.evaluate_odoo_domain(self.domain) if self.domain else []
                
                # Merge base domain with smart filter
                if smart_domain:
                    base_domain = expression.AND([base_domain, smart_domain]) if base_domain else smart_domain

                # NEW: Apply dashboard filter mappings and user filters
                base_domain = self._process_domain(base_domain, extra_action, self.group_by_id)
                
                # =============================================
                # Group By Logic
                # =============================================
                if self.group_by_id:
                    data['is_grouped'] = True
                    group_field = self.group_by_id.name
                    group_field_type = self.group_by_id.ttype
                    
                    # Determine groupby spec (handle date/datetime with time_range)
                    if group_field_type in ('date', 'datetime') and self.time_range:
                        groupby_spec = f'{group_field}:{self.time_range}'
                    else:
                        groupby_spec = group_field
                    
                    # Fetch unique groups
                    group_results = model_obj.read_group(
                        base_domain,
                        [group_field],
                        [groupby_spec],
                        orderby=f'{self.sort_field_id.name} {self.sort_order}' if self.sort_field_id else None,
                        limit=self.limit_record if self.limit_record > 0 else None
                    )
                    
                    groups_data = []
                    for grp in group_results:
                        # Get the group key/value
                        group_key = grp.get(groupby_spec) or grp.get(group_field)
                        
                        # Format group name
                        if isinstance(group_key, tuple):
                            group_name = group_key[1]  # Many2one: (id, name)
                        elif group_key is False:
                            if self.hide_false:
                                continue
                            group_name = 'Undefined'
                        else:
                            group_name = str(group_key)
                        
                        # Build group-specific domain
                        group_domain_key = grp.get('__domain', [])
                        group_base_domain = expression.AND([base_domain, group_domain_key]) if group_domain_key else base_domain
                        
                        # Calculate segments for this group
                        group_total = 0
                        group_segments = []
                        
                        # Support Live Preview for segments
                        segments = []
                        if kwargs.get('isDirty') and dirty_data.get('stacked_segment_ids'):
                            # Parse segments from dirty data (usually many2one list format)
                            raw_segments = dirty_data.get('stacked_segment_ids', [])
                            for op in raw_segments:
                                if isinstance(op, (list, tuple)) and len(op) == 3 and op[2]:
                                    segments.append(SimpleNamespace(**op[2]))
                                elif isinstance(op, dict):
                                    segments.append(SimpleNamespace(**op))
                        
                        if not segments:
                            segments = self.stacked_segment_ids.sorted('sequence')

                        for segment in segments:
                            segment_domain = self.evaluate_odoo_domain(segment.domain) if segment.domain else []
                            final_domain = expression.AND([group_base_domain, segment_domain]) if group_base_domain else segment_domain
                            
                            count = model_obj.search_count(final_domain)
                            group_total += count
                            
                            group_segments.append({
                                'id': getattr(segment, 'id', False),
                                'name': segment.name,
                                'color': getattr(segment, 'color', '#4CAF50'),
                                'value': count,
                                'domain': final_domain,
                            })
                        
                        # Calculate percentages for this group
                        for seg in group_segments:
                            seg['percentage'] = round((seg['value'] / group_total * 100), 1) if group_total > 0 else 0
                        
                        groups_data.append({
                            'name': group_name,
                            'total': group_total,
                            'segments': group_segments,
                        })
                    
                    data['groups'] = groups_data
                
                # =============================================
                # Single Aggregate Logic (No Group By)
                # =============================================
                else:
                    total_value = 0
                    segments_data = []
                    
                    # Support Live Preview for segments
                    segments = []
                    if kwargs.get('isDirty') and dirty_data.get('stacked_segment_ids'):
                        raw_segments = dirty_data.get('stacked_segment_ids', [])
                        for op in raw_segments:
                            if isinstance(op, (list, tuple)) and len(op) == 3 and op[2]:
                                segments.append(SimpleNamespace(**op[2]))
                            elif isinstance(op, dict):
                                segments.append(SimpleNamespace(**op))
                    
                    if not segments:
                        segments = self.stacked_segment_ids.sorted('sequence')

                    for segment in segments:
                        segment_domain = self.evaluate_odoo_domain(segment.domain) if segment.domain else []
                        final_domain = expression.AND([base_domain, segment_domain]) if base_domain else segment_domain
                        
                        count = model_obj.search_count(final_domain)
                        total_value += count
                        
                        segments_data.append({
                            'id': getattr(segment, 'id', False),
                            'name': segment.name,
                            'color': getattr(segment, 'color', '#4CAF50'),
                            'value': count,
                            'domain': final_domain,
                        })
                    
                    for seg in segments_data:
                        seg['percentage'] = round((seg['value'] / total_value * 100), 1) if total_value > 0 else 0
                    
                    data['segments'] = segments_data
                    data['total'] = total_value
                
            except Exception as e:
                pass
            
            return data

        return res
    
    def _evaluate_date_expression(self, expr):
        """Evaluate a date expression string and return an ISO date string (YYYY-MM-DD).
        
        Supports:
        - Direct date strings: '2026-01-01'
        - Shortcuts: start_last_month, end_last_month, start_this_month, end_this_month, today
        - Python expressions: (context_today() - relativedelta(months=1)).replace(day=1)
        """
        if not expr:
            return None
        
        expr = expr.strip()
        
        # Try direct date string first (YYYY-MM-DD)
        try:
            parsed = date.fromisoformat(expr)
            return parsed.isoformat()
        except (ValueError, TypeError):
            pass
        
        # Build evaluation context with date helpers
        today_date = fields.Datetime.context_timestamp(self, datetime.now()).date()
        
        def context_today():
            return today_date
        
        # Pre-calculate common shortcuts
        _start_last_month = (today_date - relativedelta(months=1)).replace(day=1)
        _end_last_month = today_date.replace(day=1) - timedelta(days=1)
        _start_this_month = today_date.replace(day=1)
        if today_date.month == 12:
            _end_this_month = today_date.replace(year=today_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            _end_this_month = today_date.replace(month=today_date.month + 1, day=1) - timedelta(days=1)
        
        eval_context = {
            'relativedelta': relativedelta,
            'timedelta': timedelta,
            'datetime': datetime,
            'date': date,
            'today': today_date,
            'context_today': context_today,
            # Shortcut variables
            'start_last_month': _start_last_month,
            'end_last_month': _end_last_month,
            'start_this_month': _start_this_month,
            'end_this_month': _end_this_month,
        }
        
        try:
            result = safe_eval(expr, eval_context)
            if isinstance(result, (date, datetime)):
                return result.date().isoformat() if isinstance(result, datetime) else result.isoformat()
            return str(result)
        except Exception as e:
            return None

    def _get_default_filter_label(self):
        """Get default label based on filter type"""
        labels = {
            'employee': 'Employee',
            'date_range': 'Date Range',
            'many2one': self.filter_field_id.field_description if self.filter_field_id else 'Select',
            'selection': self.filter_field_id.field_description if self.filter_field_id else 'Select',
            'manual': 'Filter',
        }
        return labels.get(self.filter_type, 'Filter')
    
    def _get_employee_options(self):
        """Get employee options for filter dropdown"""
        company_ids = self.env.user.company_ids.ids
        employees = self.env['hr.employee'].sudo().search([
            ('company_id', 'in', company_ids),
            ('active', '=', True),
        ], order='name asc')
        return [{'id': emp.id, 'name': emp.name} for emp in employees]
    
    def _get_many2one_options(self):
        """
        Get options from related model for filter dropdown, respecting filter_domain if set.
        """
        if not self.filter_model_id:
            return []
        try:
            model_obj = self.env[self.filter_model_id.model].sudo()
            domain = []
            
            # Apply Filter Domain if provided
            if self.filter_domain:
                try:
                    domain = self.evaluate_odoo_domain(self.filter_domain)
                except Exception as e:
                    pass # Ignore invalid domain to avoid crash
            
            records = model_obj.search(domain, limit=1000, order='name asc' if 'name' in model_obj._fields else None)
            return [{'id': r.id, 'name': r.display_name} for r in records]
        except Exception:
            return []
    
    def _get_selection_options(self):
        """Get selection field options for filter dropdown"""
        if not self.filter_field_id or not self.model_id:
            return []
        try:
            model_obj = self.env[self.model_id.model]
            field = model_obj._fields.get(self.filter_field_id.name)
            if field and field.type == 'selection':
                selection = field._description_selection(self.env)
                return [{'id': val, 'name': label} for val, label in selection]
        except Exception:
            pass
        return []

    def _init_configuration(self):
        """
        Configure global cong variable.
        Fully overriding base method to inject sudo() for sensitive field access (ir.model.fields).
        """
        self_sudo = self.sudo()
        conf = SimpleNamespace(
            model=self.model_id.model,
            name=self.name,
            hide_false_value=self.hide_false_value,
            show_unit=self.show_unit,
            unit_type=self.unit_type,
            custom_unit=self.custom_unit,
            color_palette=self.color_palette,
            layout_type=self.layout_type,
            tile_layout_type=self.tile_layout_type,
            meter_target=self.meter_target,
            text_align=self.text_align,
            background_color=self.background_color,
            is_kpi_border=self.is_kpi_border,
            kpi_border_type=self.kpi_border_type,
            kpi_border_color=self.kpi_border_color,
            kpi_border_width=self.kpi_border_width,
            font_color=self.font_color,
            font_size=self.font_size,
            font_weight=self.font_weight, # Keep original for compatibility
            font_weight_bold=self.font_weight_bold, # New logical field
            header_font_size=self.header_font_size,
            header_font_color=self.header_font_color,
            header_font_weight=self.header_font_weight,
            header_font_style=self.header_font_style,
            header_font_family=self.header_font_family_id.font_family_css or 'Arial',
            font_style=self.font_style,
            font_family=self.font_family_id.font_family_css or 'Arial',
            group_by=self_sudo.group_by_id.name,
            time_range=self.time_range,
            map_group_by=self_sudo.map_group_by_id.name,
            sub_group_by=self_sudo.sub_group_by_id.name,
            sub_time_range=self.sub_time_range,
            measurement_field_ids=self_sudo.measurement_field_ids,
            sort_field=self_sudo.sort_field_id.name,
            sort_order=self.sort_order,
            limit_record=self.limit_record,
            date_filter_field=self_sudo.date_filter_field_id.name,
            date_filter_option=self.date_filter_option,
            domain=self.evaluate_odoo_domain(self.domain) if self.domain else [],
            data_type=self.data_type,
            company=self.company_id.id,
            measurement_field_id=self.measurement_field_id,
            include_periods=self.include_periods,
            same_period_previous_years=self.same_period_previous_years,
            list_type=self.list_type,
            icon_option=self.icon_option,
            default_icon=self.default_icon,
            icon=self.icon,
            kpi_model=self.kpi_model_id.model,
            kpi_data_type=self.kpi_data_type,
            kpi_measurement_field_id=self.kpi_measurement_field_id,
            kpi_limit_record=self.kpi_limit_record,
            kpi_domain=self.with_context(evaluating_kpi=True).evaluate_odoo_domain(self.kpi_domain)
            if self.kpi_domain
            else [],
            kpi_date_filter_field_id=self.kpi_date_filter_field_id.name,
            kpi_date_filter_option=self.kpi_date_filter_option,
            kpi_include_periods=self.kpi_include_periods,
            kpi_same_period_previous_years=self.kpi_same_period_previous_years,
            kpi_comparison_type=self.kpi_comparison_type,
            kpi_enable_target=self.kpi_enable_target,
            kpi_target_value=self.kpi_target_value,
            kpi_view_type=self.kpi_view_type,
            previous_period_comparision=self.previous_period_comparision,
            previous_period_duration=self.previous_period_duration,
            previous_period_type=self.previous_period_type,
            is_apply_multiplier=self.is_apply_multiplier,
            todo_layout=self.todo_layout,
            todo_action_ids=[
                {
                    "name": action.name,
                    "action_line_ids": [
                        {
                            "name": action_line.name,
                            "active_record": action_line.active_record,
                        }
                        for action_line in action.action_line_ids
                    ],
                }
                for action in self.todo_action_ids
            ],
            chart_multiplier_ids=[
                {"field_id": m.field_id.id, "multiplier": m.multiplier}
                for m in self_sudo.chart_multiplier_ids
            ],
            list_measure_ids=[
                {
                    "id": m.id,
                    "list_measure_id": m.list_measure_id.id,
                    "value_type": m.value_type,
                    "measure_domain": m.measure_domain, 
                    "label_name": m.label_name,
                    "measure_color": m.measure_color or '#000000'
                }
                for m in self_sudo.list_measure_ids
            ],
            list_field_ids=[
                {"list_field_id": f.list_field_id.id, "sequence": f.sequence}
                for f in self_sudo.list_field_ids
            ],
        )
        return conf, conf.domain.copy()

    def _handle_dirty_data(self, conf, data):
        """
        Override to ensure custom fields (measure_domain, label_name) are preserved
        from the dirty data passed from the frontend.
        """
        super(DashboardChart, self)._handle_dirty_data(conf, data)
        
        if data.get('list_measure_ids'):
            raw_measures = data.get('list_measure_ids')
            processed_measures = []
            
            for m in raw_measures:
                vals = m
                if isinstance(m, (list, tuple)) and len(m) == 3 and m[0] in (0, 1):
                    vals = m[2]
                elif isinstance(m, (list, tuple)) and len(m) == 3 and m[0] == 2:
                    continue 
                    
                if isinstance(vals, dict):
                    processed_measures.append({
                        "id": vals.get('id'), 
                        "list_measure_id": vals.get('list_measure_id'),
                        "value_type": vals.get('value_type'),
                        "measure_domain": vals.get('measure_domain'),
                        "label_name": vals.get('label_name')
                    })
            
            conf.list_measure_ids = processed_measures
        
        # Handle new layout fields
        if data.get('header_font_size'):
            conf.header_font_size = data.get('header_font_size')
        if data.get('header_font_weight'):
            conf.header_font_weight = data.get('header_font_weight')
        if data.get('header_font_style'):
            conf.header_font_style = data.get('header_font_style')
        if data.get('header_font_color'):
            conf.header_font_color = data.get('header_font_color')
        if data.get('font_weight_bold'):
            conf.font_weight_bold = data.get('font_weight_bold')
        if data.get('font_style'):
            conf.font_style = data.get('font_style')
            
        if data.get('filter_date_start_default'):
            conf.filter_date_start_default = data.get('filter_date_start_default')
        if data.get('filter_date_end_default'):
            conf.filter_date_end_default = data.get('filter_date_end_default')
            
        if data.get('font_family_id'):
            font_family_id = self._normalize_m2o(data.get('font_family_id'))
            conf.font_family = self.env['tw.dashboard.font'].browse(font_family_id).font_family_css or 'Arial'
        if data.get('header_font_family_id'):
            header_font_family_id = self._normalize_m2o(data.get('header_font_family_id'))
            conf.header_font_family = self.env['tw.dashboard.font'].browse(header_font_family_id).font_family_css or 'Arial'

    def _normalize_m2o(self, value):
        return value[0] if isinstance(value, (list, tuple)) and value else value