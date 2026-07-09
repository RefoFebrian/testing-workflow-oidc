# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date,timedelta, datetime, tzinfo
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class TWBoomDashboardUser(models.Model):
    _inherit = "tw.boom.task"


    # ============================================
    # MAIN METHOD
    # ============================================
    @api.model
    def action_welcome_text(self):
        """
        Main entry point for welcome dashboard data
        Returns: dict with status, message, and data
        """
        emp = self.env.user.sudo().employee_id
        
        if not emp:
            return {
                'status': 0,
                'message': 'No employee record found for current user',
                'data': []
            }
        
        # Call separated methods
        user_info = self._get_user_info(emp)
        birthday_info = self._get_birthday_info(emp)
        
        return {
            'status': 1,
            'message': 'ok',
            'data': [user_info, birthday_info]
        }
    
    @api.model
    def action_get_employee(self):
        """
        Get list of employees in user's companies for filter dropdown
        Returns: list of dicts with id and name
        """
        # TODO: company yang diambil dari context bisa atau dari user company_ids
        company_ids = self.env.user.company_ids.ids
        # company_ids = self._context.get('allowed_company_ids', [])
        
        if not company_ids:
            return []
        
        # TODO: saat ini pencarian employee masih berdasarkan company_id,
        # tidak mencari berdasarkan job_id yang sesuai dengan master kategori
        employees = self.env['hr.employee'].sudo().search([
            ('company_id', 'in', company_ids),
            ('active', '=', True),
            ('working_end_date', '=', False)  # Only active employees
        ], order='name asc')
        
        result = []
        for emp in employees:
            result.append({
                'id': emp.id,
                'name': emp.name,
                'company_id': emp.company_id.id,
            })
        
        return result

    @api.model
    def action_task_status(self):
        """
        Get task status counts (today, now, current, overdue, etc.)
        Returns: dict with count values
        """
        emp = self.env.user.sudo().employee_id
        
        if not emp:
            return {
                'today': 0, 'now': 0, 'current': 0,
                'potensi_od': 0, 'overdue': 0,
                'overdue_now': 0, 'overdue_today': 0
            }

        # Determine query scope based on job role
        query_where, params = self._get_task_query_filter(emp)
        
        query = f"""
            SELECT 
                COUNT(tbt.id) FILTER (WHERE tbt.state = 'open' OR ((tbt.done_date)::date = (now() - interval '7 hours')::date)) AS today,
                COUNT(tbt.id) FILTER (WHERE tbt.state = 'open') AS now,
                COUNT(tbt.id) FILTER (WHERE tbt.state = 'open' AND ((now() - INTERVAL '7 hours')::date - (tbt.transaction_date ::date + tbc.due_date_day)) < -3) AS current,
                COUNT(tbt.id) FILTER (WHERE tbt.state = 'open' AND ((now() - INTERVAL '7 hours')::date - (tbt.transaction_date::date + tbc.due_date_day)) BETWEEN -3 and 0) AS potensi_od,
                COUNT(tbt.id) FILTER (WHERE tbt.state = 'open' AND ((now() - INTERVAL '7 hours')::date - (tbt.transaction_date::date + tbc.due_date_day)) >= 1) AS overdue,
                COUNT(tbt.id) FILTER (WHERE tbt.state = 'open' AND ((now() - INTERVAL '7 hours')::date - (tbt.transaction_date::date + tbc.due_date_day)) >= 1) AS overdue_now,
                COUNT(tbt.id) FILTER (WHERE 
                    (tbt.state = 'open' AND ((now() - INTERVAL '7 hours')::date - (tbt.transaction_date::date + tbc.due_date_day)) >= 1) 
                    OR ((tbt.state = 'done' AND ((now() - INTERVAL '7 hours')::date - (tbt.transaction_date::date + tbc.due_date_day)) >= 1) 
                        AND (tbt.done_date)::date = (now() - interval '7 hours')::date)
                ) AS overdue_today
            FROM tw_boom_task tbt
            LEFT JOIN tw_boom_category tbc ON tbc.id = tbt.category_id 
            WHERE 1 = 1 
            {query_where}
        """
        
        self._cr.execute(query, params)
        result = self._cr.dictfetchone()
        
        data = result or {
            'today': 0, 'now': 0, 'current': 0,
            'potensi_od': 0, 'overdue': 0,
            'overdue_now': 0, 'overdue_today': 0
        }

        return {
            'status': 1,
            'data': [data]
        }
    @api.model
    def action_task_by_category(self):
        """
        Get task counts grouped by category
        Returns: list of dicts with category names and counts
        """
        emp_obj = self.env.user.sudo().employee_id
        
        if not emp_obj:
            return []
        
        # Determine query scope based on job role
        query_where, params = self._get_task_query_filter(emp_obj)
        
        query = f"""
            SELECT 
                CONCAT(tbmc."name" , ' - ',tbc.name) as kategori_name,
                COALESCE(SUM(tbt.kat_current), 0) as kat_current,
                COALESCE(SUM(tbt.kat_potensi_od), 0) as kat_potensi_od,
                COALESCE(SUM(tbt.kat_overdue), 0) as kat_overdue
            FROM tw_boom_category tbc
            LEFT JOIN tw_boom_main_category tbmc ON tbmc.id = tbc.main_category_id 
            LEFT JOIN LATERAL(
                SELECT tbt.category_id,
                    SUM(CASE
                        WHEN ((now() - INTERVAL '7 hours')::date - (tbt.transaction_date::date + tbc.due_date_day)) < -3 THEN 1
                        ELSE 0
                    END) AS kat_current,
                    SUM(CASE
                        WHEN (now() - INTERVAL '7 hours')::date - (tbt.transaction_date::date + tbc.due_date_day)::DATE BETWEEN -3 and 0 THEN 1
                        ELSE 0
                    END) AS kat_potensi_od,
                    SUM(CASE
                        WHEN ((now() - INTERVAL '7 hours')::date - (tbt.transaction_date::date + tbc.due_date_day)) >= 1 THEN 1
                        ELSE 0
                    END) AS kat_overdue
                FROM tw_boom_task tbt
                WHERE 1 = 1
                AND tbt.state = 'open'
                {query_where}
                GROUP BY tbt.category_id
            ) tbt on tbt.category_id = tbc.id
            GROUP BY CONCAT(tbmc."name" , ' - ',tbc.name)
            HAVING COALESCE(SUM(tbt.kat_overdue), 0) > 0 
                OR COALESCE(SUM(tbt.kat_potensi_od), 0) > 0 
                OR COALESCE(SUM(tbt.kat_current), 0) > 0
            ORDER BY kat_overdue DESC, kat_potensi_od DESC
        """
        
        self._cr.execute(query, params)
        results = self._cr.dictfetchall()
        
        return {
            'status': 1,
            'data': results
        }

    @api.model
    def action_task_done(self):
        emp_obj = self.env.user.sudo().employee_id
        
        if not emp_obj:
            return []
        
        # Determine query scope based on job role
        query_where, params = self._get_task_query_filter(emp_obj)

        query = f"""
            SELECT 
                COUNT(tbt.id) FILTER (WHERE tbt.state = 'open' OR ((tbt.done_date)::date = (now() - interval '7 hours')::date)) AS today,
                COUNT(tbt.id) FILTER (WHERE tbt.state = 'done' AND ((tbt.done_date)::date = (now() - interval '7 hours')::date)) AS done,
                COUNT(tbt.id) FILTER (where tbt.state = 'done' AND ((tbt.done_date)::date = (now() - interval '7 hours')::date) AND ((now() - INTERVAL '7 hours')::date - (tbt.transaction_date::date + tbc.due_date_day)) < 1) AS done_current,
                COUNT(tbt.id) FILTER (where tbt.state = 'done' AND ((tbt.done_date)::date = (now() - interval '7 hours')::date) AND ((now() - INTERVAL '7 hours')::date - (tbt.transaction_date::date + tbc.due_date_day)) >= 1) AS done_overdue
            FROM tw_boom_task tbt
            LEFT JOIN tw_boom_category tbc ON tbc.id = tbt.category_id 
            WHERE 1=1 
            {query_where}
        """
        self._cr.execute(query, params)
        results = self._cr.dictfetchall()
        
        return results

    @api.model
    def action_task_ages(self):
        emp_obj = self.env.user.sudo().employee_id
        
        if not emp_obj:
            return []
        
        # Determine query scope based on job role
        query_where, params = self._get_task_query_filter(emp_obj)

        query = f"""
            SELECT SUM(
                    CASE
                        WHEN (now() - INTERVAL '7 hours')::date - (task.transaction_date::date + categ.due_date_day)::DATE < -3 THEN 1
                        ELSE 0
                    END
                ) AS curr,
                SUM(
                    CASE
                        WHEN (now() - INTERVAL '7 hours')::date - (task.transaction_date::date + categ.due_date_day)::DATE BETWEEN -3 and 0 THEN 1
                        ELSE 0
                    END
                ) AS potensi_od,
                SUM(
                    CASE
                        WHEN (now() - INTERVAL '7 hours')::date - (task.transaction_date::date + categ.due_date_day)::DATE >= 1 THEN 1
                        ELSE 0
                    END
                ) AS overdue
            FROM tw_boom_task task
                LEFT JOIN tw_boom_category categ ON categ.id = task.category_id 
            WHERE task.state = 'open'
                {query_where}
        """
        self._cr.execute(query, params)
        result = self._cr.dictfetchone()
        
        # Return with default values if no data
        return result or {
            'curr': 0,
            'potensi_od': 0,
            'overdue': 0
        }

    @api.model
    def action_boom_leader_board(self):
        """
        Get leaderboard data for employees in the area
        Currently shows basic ranking by task completion
        TODO: Implement proper point system once flow is defined
        
        Returns: list of dicts with name, img_path, point, rank
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        emp_obj = self.env.user.sudo().employee_id
        
        if not emp_obj:
            return []
        
        # Get employees in same area/companies
        emp_ids = self._get_leaderboard_employees(emp_obj)
        
        if not emp_ids:
            return []
        
        # Get date range (last month)
        start_date, end_date = self._get_last_month_range()
        
        # Build leaderboard query
        # NOTE: Currently using 0 as placeholder for points
        # Will be replaced with actual point calculation once flow is defined

        query = """
            SELECT DISTINCT CONCAT(he.name, ' - ', rc.name) AS name,
                CONCAT(%s, '/web/image?model=res.users&id=', ru.id, '&field=image_1920') AS img_path,
                0 AS point
            FROM hr_employee he
            LEFT JOIN res_company rc ON rc.id = he.company_id
            LEFT JOIN resource_resource rr ON rr.id = he.resource_id
            LEFT JOIN res_users ru ON ru.id = rr.user_id
            LEFT JOIN tw_boom_task tbt ON tbt.employee_id = he.id
            WHERE he.id IN %s
            AND he.working_end_date IS NULL
            ORDER BY point DESC
        """
        
        self._cr.execute(query, (base_url, tuple(emp_ids)))
        results = self._cr.dictfetchall()

        return results

    @api.model
    def action_task_list_by_status(self):
        """
        Get task list filtered by status
        
        Args:
            status_filter: str - 'potensi_od', 'overdue', 'current'
        Returns: list of dicts
        """
        emp_obj = self.env.user.sudo().employee_id
        
        if not emp_obj:
            return []
        
        # Determine query scope based on job role
        query_where, params = self._get_task_query_filter(emp_obj)
        
        # Get base URL for transaction links
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        
        # Get company/branch code safely
        company_code = self._get_user_company_code()
        
        # Add company code to params
        params.insert(0, base_url)
        params.insert(0, company_code)
        
        query = f"""
            SELECT 
                %s AS branch_code,
                emp.name AS employee_name,
                task.no_transaction,
                task.id_transaction,
                im.model,
                %s AS base_url,
                CASE
                    WHEN (now() - INTERVAL '7 hours')::date - (task.transaction_date::date + categ.due_date_day)::DATE < -3 THEN 'Current'
                    WHEN (now() - INTERVAL '7 hours')::date - (task.transaction_date::date + categ.due_date_day)::DATE BETWEEN -3 and 0 THEN 'Potensi OD'
                    ELSE 'Overdue'
                END AS state,
                ((now() - INTERVAL '7 hours')::date - (task.transaction_date::date + categ.due_date_day)::DATE) AS days_diff,
                categ.periode,
                main."name" AS klasifikasi,
                sub."name" AS sub_kategori,
                categ."name" AS misi,
                task.transaction_date,
                task.done_date AS date_done,
                task.transaction_value AS value
            FROM tw_boom_task task
            LEFT JOIN res_company rc ON rc.id = task.company_id
            LEFT JOIN hr_employee emp ON emp.id = task.employee_id
            LEFT JOIN tw_boom_category categ ON categ.id = task.category_id 
            LEFT JOIN tw_boom_main_category main ON main.id = task.main_category_id 
            LEFT JOIN tw_boom_sub_category sub ON sub.id = task.sub_category_id 
            LEFT JOIN ir_model im ON im.id = task.model_id 
            WHERE task.state = 'open'
            {query_where}
            ORDER BY days_diff DESC, task.transaction_date ASC
        """
        self._cr.execute(query, params)
        result = self._cr.dictfetchall()

        return result

    # ============================================
    # PRIVATE HELPER METHODS
    # ============================================
    
    def _get_user_info(self, employee):
        """
        Get user basic info with greeting and quote
        Args:
            employee: hr.employee record
        Returns: dict with name, job, greet, quotes, author, message
        """
        name = employee.name
        job_name = employee.job_id.name or ''
        greet = self._get_greeting()
        message = self._get_birthday_message(employee)
        quote_data = self._get_daily_quote()
        
        return {
            'name': name,
            'job': job_name,
            'greet': greet,
            'quotes': quote_data.get('quote', ''),
            'author': quote_data.get('author', ''),
            'message': message
        }
    
    def _get_greeting(self):
        """
        Get time-based greeting (Pagi/Siang/Sore/Malam)
        Returns: str
        """
        now = datetime.now() + relativedelta(hours=7)
        
        if 12 < now.hour <= 15:
            return 'Siang'
        elif 15 < now.hour <= 18:
            return 'Sore'
        elif 18 < now.hour < 24:
            return 'Malam'
        else:
            return 'Pagi'
    
    def _get_birthday_message(self, employee):
        """
        Get birthday message for current employee
        Args:
            employee: hr.employee record
        Returns: str
        """
        if not employee.birthday:
            return 'Apa kabar hari ini?'
        
        now = datetime.now() + relativedelta(hours=7)
        if employee.birthday.day == now.day and employee.birthday.month == now.month:
            return f'Selamat Ulang Tahun {employee.name}!'
        
        return 'Apa kabar hari ini?'
    
    def _get_birthday_info(self, employee):
        """
        Get birthday information for all employees
        Args:
            employee: hr.employee record (current user)
        Returns: dict with birthday flags and lists
        """
        now = datetime.now() + relativedelta(hours=7)
        company_id = employee.company_id.id or 0
        
        # Check if current employee has birthday today
        has_birthday = False
        if employee.birthday:
            has_birthday = (employee.birthday.day == now.day and 
                          employee.birthday.month == now.month)
        
        # Get other employees with birthday today
        other_birthdays = self._get_branch_birthdays(now.month, now.day)
        
        # Get colleagues in same branch with birthday today
        colleagues_birthdays = self._get_colleague_birthdays(employee.id, company_id, now.month, now.day)
        
        return {
            'birthday': has_birthday,
            'other_birthday': other_birthdays,
            'notified': colleagues_birthdays
        }
    
    def _get_branch_birthdays(self, month, day):
        """
        Get all employees in user's branches with birthday on specific date
        Args:
            month: int
            day: int
        Returns: list of dicts
        """
        company_ids = self.env.user.company_ids.ids
        if not company_ids:
            return []
        
        # Build SQL condition for branches
        if len(company_ids) == 1:
            company_condition = f"= {company_ids[0]}"
        else:
            company_condition = f"IN {tuple(company_ids)}"
        
        query = f"""
            SELECT he.id
                , he.name
                , rc.name AS company
                , hj.name->>'en_US' AS job
            FROM hr_employee he
            LEFT JOIN res_company rc ON rc.id = he.company_id
            LEFT JOIN hr_job hj ON hj.id = he.job_id 
            WHERE EXTRACT(month from he.birthday) = %s
            AND EXTRACT(day from he.birthday) = %s
            AND he.company_id {company_condition}
            AND he.working_end_date IS NULL
        """
        
        self._cr.execute(query, (month, day))
        return self._cr.dictfetchall()
    
    def _get_colleague_birthdays(self, current_employee_id, company_id, month, day):
        """
        Get colleagues in same branch with birthday on specific date
        Args:
            current_employee_id: int
            company_id: int
            month: int
            day: int
        Returns: list of lists [name, registry_number, job]
        """
        colleagues = self.env['hr.employee'].sudo().search([
            ('company_id', '=', company_id),
            ('id', '!=', current_employee_id),
            ('birthday', '!=', False)
        ])
        
        result = []
        for colleague in colleagues:
            if colleague.birthday.month == month and colleague.birthday.day == day:
                result.append([
                    colleague.name,
                    colleague.registry_number,
                    colleague.job_id.name or ''
                ])
        
        return result
    
    def _get_daily_quote(self):
        """
        Get motivational quote for today
        Returns: dict with 'quote' and 'author' keys
        """
        today_date = date.today()
        
        quotes = self.env['tw.boom.master.quotes'].sudo().search([
            ('is_active', '=', True),
            ('category', '!=', False)
        ])
        
        if not quotes:
            return {'quote': '', 'author': ''}
        
        # Sort by priority
        sorted_quotes = sorted(quotes, key=lambda q: (
            {'specific_date': 1, 'specific_day': 2, 'random': 3}.get(q.category, 4),
            q.start_date if q.category == 'specific_date' else datetime.min.date(),
            q.day_name if q.category == 'specific_day' else ''
        ))
        
        selected_quotes = self._filter_quotes_by_date(sorted_quotes, today_date)
        
        # Fallback to random quotes
        if not selected_quotes:
            selected_quotes = [q for q in sorted_quotes if q.category == 'random']
        
        if not selected_quotes:
            return {'quote': '', 'author': ''}
        
        # Select based on current second for variety
        current_second = datetime.now().second
        selected_index = current_second % len(selected_quotes)
        selected_quote = selected_quotes[selected_index]
        
        return {
            'quote': selected_quote.name or '',
            'author': selected_quote.author or ''
        }
    
    def _filter_quotes_by_date(self, quotes, target_date):
        """
        Filter quotes based on category rules
        Args:
            quotes: list of dms.master.quotes records
            target_date: date object
        Returns: list of filtered quotes
        """
        result = []
        day_name = target_date.strftime('%A')
        
        for quote in quotes:
            if quote.category == 'specific_date':
                if quote.start_date and quote.end_date:
                    if quote.start_date <= target_date <= quote.end_date:
                        result.append(quote)
            elif quote.category == 'specific_day':
                if quote.day_name == day_name:
                    result.append(quote)
        
        return result

    def _get_task_query_filter(self, employee):
        """
        Get query filter based on employee role
        Returns: tuple (query_where_string, params_list)
        """
        if not employee:
            return "", []
        
        # Check if user is Administration Head
        if employee.job_id and self._is_administration_head(employee.job_id):
            # Show all tasks in user's companies
            company_ids = self.env.user.company_ids.ids
            
            if not company_ids:
                return " AND tbt.employee_id = %s", [employee.id]
            
            if len(company_ids) == 1:
                return " AND tbt.company_id = %s", [company_ids[0]]
            else:
                return " AND tbt.company_id IN %s", [tuple(company_ids)]
        else:
            # Show only employee's own tasks
            return " AND tbt.employee_id = %s", [employee.id]

    def _is_administration_head(self, job):
        """
        Check if job is Administration Head
        Args:
            job: hr.job record
        Returns: bool
        """
        if not job or not job.name:
            return False
        
        # Check multiple possible variations
        job_name_lower = job.name.lower().strip()
        admin_head_variations = [
            'administration head',
            'admin head',
            'head of administration',
            'kepala administrasi'
        ]
        
        return job_name_lower in admin_head_variations

    def _get_leaderboard_employees(self, employee):
        """
        Get list of employee IDs for leaderboard based on current employee's area
        
        Args:
            employee: hr.employee record
        Returns: list of employee IDs
        """
        # Get companies in employee's area
        if hasattr(employee, 'area_id') and employee.area_id:
            company_ids = employee.area_id.company_ids.ids
        else:
            # Fallback: use employee's own company
            company_ids = [employee.company_id.id] if employee.company_id else []
        
        if not company_ids:
            return []
        
        # Get all active employees in those companies
        employees = self.env['hr.employee'].sudo().search([
            ('company_id', 'in', company_ids),
            ('working_end_date', '=', False)  # Only active employees
        ])
            
        return employees.ids if employees else []

    def _get_last_month_range(self):
        """
        Get date range for last month
        Returns: tuple (start_date, end_date)
        """
        today = datetime.today()
        first_day_this_month = datetime(today.year, today.month, 1)
        start_date = first_day_this_month - relativedelta(months=1)
        end_date = first_day_this_month - timedelta(seconds=1)
        
        return start_date, end_date

    def _get_user_company_code(self):
        """
        Safely get user's company code
        Returns: str (company code or empty string)
        """
        user = self.env.user
        
        # Try to get from employee's company
        emp = user.sudo().employee_id
        if emp and emp.company_id:
            company = emp.company_id
            # Check if company has code field
            if hasattr(company, 'code') and company.code:
                return company.code
        
        # Try to get from user's first company
        if user.company_ids:
            company = user.company_ids[0]
            if hasattr(company, 'code') and company.code:
                return company.code
        
        # Fallback: return company name or empty
        if user.company_id:
            return user.company_id.name or ''
        
        return ''

    # ============================================
    # OPTIONAL: Individual endpoint methods
    # For frontend to call separately if needed
    # ============================================
    
    @api.model
    def get_greeting_only(self):
        """Endpoint for getting just the greeting"""
        return {'greet': self._get_greeting()}
    
    @api.model
    def get_quote_only(self):
        """Endpoint for getting just the daily quote"""
        return self._get_daily_quote()
    
    @api.model
    def get_birthdays_only(self):
        """Endpoint for getting just birthday info"""
        emp = self.env.user.sudo().employee_id
        if not emp:
            return {'birthday': False, 'other_birthday': [], 'notified': []}
        
        data = self._get_birthday_info(emp)
        data['message'] = self._get_birthday_message(emp)
        return data