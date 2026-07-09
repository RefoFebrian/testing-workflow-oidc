# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date, timedelta

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError as Warning

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class LeadSummaryReportWizard(models.TransientModel):
    _name = "tw.lead.summary.report.wizard"
    _description = "Lead Summary Report Wizard"

    # 7: defaults methods
    def _get_default_date_from(self):
        return date.today().replace(day=1)
    
    def _get_default_date_to(self):
        return date.today()
    
    def _get_default_company(self):
        return self.env.company.id
    
    # 8: fields
    name = fields.Char('Filename')
    date_from = fields.Date('From Date', required=True, default=_get_default_date_from)
    date_to = fields.Date('To Date', required=True, default=_get_default_date_to)
    company_id = fields.Many2one('res.company', string="Branch", default=_get_default_company, required=True)
    user_ids = fields.Many2many('res.users', string='Salesperson(s)')
    team_id = fields.Many2one('crm.team', string='Sales Team')
    
    # 9: compute, inverse, onchange methods
    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            return {'domain': {'user_ids': [('sale_team_id', '=', self.team_id.id)]}}
        return {}
    
    def _check_access_rights(self):
        """Check if user has access to view this report"""
        if not self.env.user.has_group('sales_team.group_sale_salesman'):
            raise AccessError(_("You don't have access to this report."))
        
    def _get_report_data(self):
        self.ensure_one()
        self._check_access_rights()
        
        # Use read-only cursor for better performance
        cr = self._cr
        
        # Build WHERE clause directly for better control
        where_clause = []
        params = []
        
        # Add date range with timezone conversion for Indonesia (WIB = UTC+7)
        where_clause.append("(l.create_date + INTERVAL '7 hours')::date BETWEEN %s AND %s")
        params.extend([self.date_from, self.date_to])
        
        # Add company filter
        where_clause.append("l.company_id = %s")
        params.append(self.company_id.id)
        
        # Add team filter if selected
        if self.team_id:
            where_clause.append("l.team_id = %s")
            params.append(self.team_id.id)
        # Or apply user's team filter if not manager
        elif not self.env.user.has_group('sales_team.group_sale_manager') and self.env.user.sale_team_id:
            where_clause.append("l.team_id = %s")
            params.append(self.env.user.sale_team_id.id)
            
        # Add salesperson filter if selected
        if self.user_ids:
            # Get employee IDs from users
            employee_ids = self.env['hr.employee'].search([('user_id', 'in', self.user_ids.ids)]).ids
            if employee_ids:
                where_clause.append("l.sales_id = ANY(%s)")
                params.append(employee_ids)
            
        where_clause = " AND ".join(where_clause) if where_clause else "1=1"
        
        # Main optimized SQL query with materialized CTE for better performance
        query = """
        WITH lead_stats AS (
            SELECT 
                l.sales_id,
                s.name as salesperson_name,
                sc.id as sales_coordinator_id,
                sc.name as sales_coordinator_name,
                b.id as company_id,
                b.name as branch_name,
                st.name as team_name,
                COUNT(*) as total_leads,
                COUNT(CASE WHEN stg.name::text ILIKE '%%new%%' THEN 1 END) as new_count,
                COUNT(CASE WHEN stg.name::text ILIKE '%%qualif%%' THEN 1 END) as qualified_count,
                COUNT(CASE WHEN stg.name::text ILIKE '%%propos%%' THEN 1 END) as proposition_count,
                COUNT(CASE WHEN stg.name::text ILIKE '%%won%%' OR stg.name::text ILIKE '%%win%%' THEN 1 END) as won_count,
                COUNT(CASE WHEN stg.name::text ILIKE '%%lost%%' THEN 1 END) as lost_count
            FROM tw_lead l
            LEFT JOIN hr_employee s ON l.sales_id = s.id
            LEFT JOIN hr_employee sc ON l.sales_coordinator_id = sc.id
            LEFT JOIN res_company b ON l.company_id = b.id
            LEFT JOIN crm_stage stg ON l.stage_id = stg.id
            LEFT JOIN res_users u ON s.user_id = u.id
            LEFT JOIN crm_team st ON l.team_id = st.id
            WHERE {}
            GROUP BY l.sales_id, s.name, sc.id, sc.name, b.id, b.name, st.name
            HAVING COUNT(*) > 0
        )
        SELECT 
            sales_id,
            salesperson_name,
            sales_coordinator_id,
            sales_coordinator_name,
            company_id,
            branch_name,
            team_name,
            total_leads,
            new_count,
            qualified_count,
            proposition_count,
            won_count,
            lost_count,
            CASE 
                WHEN total_leads > 0 THEN ROUND((won_count::float / total_leads * 100)::numeric, 2)
                ELSE 0 
            END as conversion_rate
        FROM lead_stats
        ORDER BY salesperson_name
        LIMIT 10000  -- Prevent excessive memory usage
        """.format(where_clause or '1=1')
        
        # Execute with server-side cursor for large results
        cr.execute("DECLARE cur CURSOR FOR " + query, params)
        
        # Fetch in batches to reduce memory usage
        batch_size = 1000
        results = []
        while True:
            cr.execute("FETCH %d FROM cur" % batch_size)
            batch = cr.dictfetchall()
            if not batch:
                break
            results.extend(batch)
        
        return results
    
    # 10: action methods
    def _format_value(self, value, field_type=str):
        """
        Format value to ensure it's serializable
        
        Args:
            value: The value to format
            field_type: The desired output type (str, int, float, bool)
        """
        if value is None:
            if field_type in (int, float):
                return 0
            elif field_type is bool:
                return False
            return ''
            
        if isinstance(value, dict):
            # Get the English value if available, otherwise first value
            value = value.get('en_US') or next(iter(value.values()), '')
            
        try:
            if field_type is str:
                return str(value) if value is not None else ''
            elif field_type is int:
                return int(float(value or 0))
            elif field_type is float:
                return float(value or 0.0)
            elif field_type is bool:
                return bool(value)
            return str(value)
        except (ValueError, TypeError):
            if field_type in (int, float):
                return 0 if field_type is int else 0.0
            elif field_type is bool:
                return False
            return ''

    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.date_from, self.date_to)
        self.ensure_one()
        
        if self.date_from > self.date_to:
            raise ValidationError(_("Start Date must be before End Date"))
        
        # Get report data using SQL query
        report_data = self._get_report_data()
        formatted_data = []
        
        # Format the data and ensure all values are serializable
        for item in report_data:
            formatted_item = {
                'sales_id': self._format_value(item.get('sales_id'), int),
                'salesperson_name': self._format_value(item.get('salesperson_name')),
                'sales_coordinator_id': self._format_value(item.get('sales_coordinator_id'), int),
                'sales_coordinator_name': self._format_value(item.get('sales_coordinator_name')),
                'company_id': self._format_value(item.get('company_id'), int),
                'branch_name': self._format_value(item.get('branch_name')),
                'team_name': self._format_value(item.get('team_name')),
                'total_leads': self._format_value(item.get('total_leads'), int),
                'new_count': self._format_value(item.get('new_count'), int),
                'qualified_count': self._format_value(item.get('qualified_count'), int),
                'proposition_count': self._format_value(item.get('proposition_count'), int),
                'won_count': self._format_value(item.get('won_count'), int),
                'lost_count': self._format_value(item.get('lost_count'), int),
                'conversion_rate': self._format_value(item.get('conversion_rate'), float)
            }
            formatted_data.append(formatted_item)
        
        # Calculate totals in a single loop
        if formatted_data:
            total_leads = total_new = total_qualified = 0
            total_proposition = total_won = total_lost = 0

            for item in formatted_data:
                total_leads += item['total_leads']
                total_new += item['new_count']
                total_qualified += item['qualified_count']
                total_proposition += item['proposition_count']
                total_won += item['won_count']
                total_lost += item['lost_count']
            
            conversion_rate = round((total_won / total_leads * 100), 2) if total_leads > 0 else 0.0
            
            formatted_data.append({
                'sales_id': '',
                'salesperson_name': 'TOTAL',
                'sales_coordinator_id': '',
                'sales_coordinator_name': '',
                'company_id': '',
                'branch_name': '',
                'team_name': '',
                'total_leads': total_leads,
                'new_count': total_new,
                'qualified_count': total_qualified,
                'proposition_count': total_proposition,
                'won_count': total_won,
                'lost_count': total_lost,
                'conversion_rate': conversion_rate
            })
        
        # Generate report
        report_name = f"Lead_Summary_Report_{self.date_from.strftime('%Y%m%d')}_to_{self.date_to.strftime('%Y%m%d')}"
        return self.env['web.report'].sudo().generate_report(report_name, formatted_data)
    
    
