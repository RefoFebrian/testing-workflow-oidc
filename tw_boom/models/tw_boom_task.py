# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import traceback
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib

class TWBoomTask(models.Model):
    _name = "tw.boom.task"
    _description = "TW Boom Task"
    _order = "id desc"

    # 7: defaults methods

    # 8: fields
    name = fields.Char('Name')
    no_transaction = fields.Char('No Transaksi')
    source_transaction = fields.Char('Sumber Transaksi')
    id_transaction = fields.Char('ID Transaksi')
    customer_name = fields.Char(string='Customer Name')
    category_name = fields.Char(string='Kategori Task', compute='_compute_category_name')

    note_delegate = fields.Text(string="Note Delegasi", help="")

    transaction_date = fields.Datetime('Tanggal Transaksi')
    last_escalation_date = fields.Datetime('Tgl Eskalasi Terakhir')
    done_date = fields.Datetime('Tgl Selesai')
    due_date = fields.Datetime('Tgl Jatuh Tempo')

    transaction_value = fields.Float('Nilai Transaksi')

    current_escalation = fields.Char(compute='_compute_current_eskalasi', string='Current Eskalasi', help='', store=True)

    state = fields.Selection([
        ('open', 'Open'),
        ('done', 'Done'),
    ], string='Status', default='open')

    task_status = fields.Selection([
        ('current', 'Current'),
        ('potensi_overdue', 'Potensi Overdue'),
        ('overdue_1', 'Overdue H+1'),
        ('overdue_2', 'Overdue > H+1'),
    ], string='Task Status', compute='_compute_task_status', store=True)

    pic_status = fields.Selection([
        ('current_pic', 'Current PIC'),
        ('delegated', 'Delegated'),
    ], string='PIC Status', default='current_pic')

    # Field for Dashboard BOOM
    # TODO: 11/20/2025 Dashboard boom is still TBD (to be discussed)
    # bill_date = fields.Datetime('Tanggal Tagihan')
    
    # 9: relation fields
    model_id = fields.Many2one('ir.model', 'Model Transaksi')
    product_id = fields.Many2one('product.product', 'Product')
    product_color_id = fields.Many2one('product.attribute.value', 'Warna')
    lot_id = fields.Many2one('stock.lot', 'No Mesin')

    category_id = fields.Many2one('tw.boom.category', 'Kategori')
    sub_category_id = fields.Many2one('tw.boom.sub.category', 'Sub Kategori')
    main_category_id = fields.Many2one('tw.boom.main.category', 'Main Kategori')
    
    company_id = fields.Many2one('res.company', 'Branch')
    employee_id = fields.Many2one('hr.employee', 'PIC')
    previous_employee_id = fields.Many2one('hr.employee', 'PIC Sebelumnya')
    job_id = fields.Many2one('hr.job', 'PIC Job')
    job_delegation_id = fields.Many2one('hr.job', 'Job Delegasi')
    finco_id = fields.Many2one('res.partner', 'Finance Company', domain=[('category_id.name', '=', 'Finance Company')])
    customer_id = fields.Many2one('res.partner', 'Customer')

    # Fields for filter purpose only 
    admin_spv_id = fields.Many2one('hr.employee', 'Administrasi SPV', compute='_compute_area_id', store=True)
    area_manager_id = fields.Many2one('hr.employee', 'Area Manager', compute='_compute_area_id', store=True)
    admin_manager_id = fields.Many2one('hr.employee', 'Administrasi Manager', compute='_compute_area_id', store=True)
    area_id = fields.Many2one('res.area', 'Area', compute='_compute_area_id', store=True)

    performance_status = fields.Selection([
        ('current', 'Current'),
        ('overdue_1', 'H+1'),
        ('overdue_2', '> H+1'),
    ], string='Performance Status', compute='_compute_performance_status', store=True)

    escalation_transaction_ids = fields.One2many('tw.boom.task.escalation', 'task_id', 'Eskalasi')
    history_user_ids = fields.One2many('tw.boom.task.history.user', 'task_id', 'History User')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('category_id')
    def _compute_category_name(self):
        for data in self:
            if data.category_id:
                data.category_name = data.category_id.name

    @api.depends('employee_id', 'company_id')
    def _compute_area_id(self):
        self_sudo = self.sudo()
        # Fetch Job Titles once (outside loop for performance)
        spv_job = self_sudo.env['hr.job'].search([('name', '=', 'ADMINISTRATION SPV')], limit=1)
        am_job = self_sudo.env['hr.job'].search([('name', '=', 'AREA MANAGER')], limit=1)
        adm_job = self_sudo.env['hr.job'].search([('name', '=', 'ADMINISTRATION MANAGER')], limit=1)

        valid_jobs = (spv_job | am_job | adm_job)
        cache = {}

        for data in self:
            # PIC's direct area
            data.area_id = data.employee_id.area_id if data.employee_id else False

            if not data.company_id:
                data.admin_spv_id = False
                data.area_manager_id = False
                data.admin_manager_id = False
                continue

            cid = data.company_id.id
            if cid not in cache:
                # Find employees who "own" this branch via Area, User access, or direct Company
                managers = self_sudo.env['hr.employee'].search([
                    ('job_id', 'in', valid_jobs.ids),
                    '|', '|',
                    ('area_id.company_ids', 'in', cid),
                    ('user_id.company_ids', 'in', cid),
                    ('company_id', '=', cid),
                    ('active', '=', True),
                    ('working_end_date', '=', False)
                ])
                cache[cid] = {
                    'spv': managers.filtered(lambda e: e.job_id == spv_job)[:1],
                    'am': managers.filtered(lambda e: e.job_id == am_job)[:1],
                    'adm': managers.filtered(lambda e: e.job_id == adm_job)[:1],
                }

            res = cache[cid]
            data.admin_spv_id = res['spv']
            data.area_manager_id = res['am']
            data.admin_manager_id = res['adm']

    @api.depends('state', 'done_date', 'due_date', 'transaction_date', 'category_id.due_date_day')
    def _compute_performance_status(self):
        for data in self:
            if data.state != 'done' or not data.done_date:
                data.performance_status = False
                continue
            
            # Use done_date as the point of performance capture
            reference_date = data.done_date
            
            due_date = data.due_date
            if not due_date and data.category_id and data.transaction_date:
                due_date = data.transaction_date + timedelta(days=data.category_id.due_date_day)
                
            if not due_date:
                data.performance_status = 'current'
                continue
                
            # Compare dates only for grouping purposes
            status_date = (reference_date.date() - due_date.date()).days
            
            if status_date <= 0:
                data.performance_status = 'current'
            elif status_date == 1:
                data.performance_status = 'overdue_1'
            else:
                data.performance_status = 'overdue_2'

    @api.depends('category_id', 'escalation_transaction_ids')
    def _compute_task_status(self):
        for data in self:
            due_date_value = False
            category_obj = data.category_id
            if category_obj and data.transaction_date:
                due_date_value = category_obj.due_date_day
                today = datetime.strptime((datetime.now()).strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')
                tgl_transaksi = (data.transaction_date).strftime("%Y-%m-%d %H:%M:%S")
                if data.due_date:
                    plus_due_date = data.due_date
                else:
                    plus_due_date = tgl_transaksi + timedelta(days=due_date_value)

                status_date = (today - plus_due_date).days
                if status_date < -3:
                    data.task_status = 'current'
                elif -3 <= status_date <= 0:
                    data.task_status = 'potensi_overdue'
                elif status_date == 1:
                    data.task_status = 'overdue_1'
                else:
                    data.task_status = 'overdue_2'
            else:
                data.task_status = 'overdue_2'

    @api.depends('escalation_transaction_ids')
    def _compute_current_eskalasi(self):
        for data in self:
            level = ''
            if data.escalation_transaction_ids:
                # Find the escalation with the highest interval
                # Note: This logic assumes we want the highest INTERVAL regardless of unit mixing (which shouldn't happen usually)
                max_escalation = data.escalation_transaction_ids.sorted(key=lambda r: r.interval, reverse=True)[:1]
                if max_escalation:
                    if max_escalation.unit == 'day':
                        level = f"H+{max_escalation.interval}"
                    elif max_escalation.unit == 'week':
                        level = f"W+{max_escalation.interval}"
                    elif max_escalation.unit == 'month':
                        level = f"M+{max_escalation.interval}"

                    data.current_escalation = level
                else:
                    data.current_escalation = ''
            else:
                data.current_escalation = ''

    # 12: override methods
    @api.model_create_multi
    def create(self, vals):
        for data in vals:
            category = self.env['tw.boom.category'].browse(data.get('category_id'))
            code = f"BOOM/{category.name}/"
            data['name'] = self.env['ir.sequence'].get_sequence_code_only(code)
            
        create = super(TWBoomTask, self).create(vals)
        for data in create:
            if data.employee_id:
                self.env['tw.boom.task.history.user'].suspend_security().create({
                    'task_id': data.id,
                    'employee_id': data.employee_id.id,
                    'job_id': data.employee_id.job_id.id,
                    'company_id': data.employee_id.company_id.id,
                    'assign_date': datetime.now(),
                })
        return create

    # 13: action methods
    def action_update_task_status(self):
        tasks = self.env['tw.boom.task'].search([])
        tasks._compute_task_status()

    def action_open_transaction(self):
        self.ensure_one()
        if not self.model_id or not self.id_transaction:
            return
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.model_id.model,
            'res_id': int(self.id_transaction),
            'views': [(False, 'form')],
            'target': 'current',
            'flags': {'mode': 'readonly'}
        }

    def action_tw_boom_task(self, params=None):
        name = 'BOOM Task'
        company_ids = self.env.user.company_ids
        domain = [
            ('company_id', 'in', company_ids.mapped('id')),
            ('job_id', '=', self.env.user.employee_id.job_id.id),
        ]
        if self.env.user.has_group('tw_boom.group_tw_boom_task_super_user'):
            domain = []

        if params:
            if params.get('done_delegate'):
                name = "BOOM Task Done Delegate"
                domain += [('pic_status', '=', 'delegated')]
        
        list_id = self.env.ref('tw_boom.view_tw_boom_task_list').id
        form_id = self.env.ref('tw_boom.view_tw_boom_task_form').id
        search_id = self.env.ref('tw_boom.view_tw_boom_task_filter').id
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.boom.task',
            'search_view_id': search_id,
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
            'context': {
                'search_default_group_by_state': 1,
            }
        }

    # 14: private methods
    
    # Update PIC Task cause by Mutation Branch or Resignation
    def update_task_pic(self, limit=None):
        query_limit = ""
        if limit:
            query_limit += f" LIMIT {limit}"

        get_tasklist = f"""
            SELECT
                task.id as task_id,
                task.company_id as task_branch,
                pic.name as prev_pic,
                new_pic.pic_id as new_pic_id,
                new_pic.job_id as new_pic_job_id,
                new_pic.pic_name as new_pic,
                CASE
                    WHEN task.company_id != pic.company_id THEN 'mutation'
                    WHEN pic.working_end_date IS NOT NULL THEN 'resign'
                    ELSE 'unknown'
                END as update_reason
            FROM tw_boom_task task
            LEFT JOIN tw_boom_category kateg ON kateg.id = task.category_id
            LEFT JOIN hr_employee pic ON task.employee_id = pic.id
            LEFT JOIN LATERAL (
                SELECT
                    he.id as pic_id,
                    he.company_id as branch_id,
                    he.job_id as job_id,
                    he.name as pic_name
                FROM hr_employee he
                WHERE he.company_id = task.company_id
                AND he.job_id = kateg.job_id
                AND he.working_end_date IS NULL
                AND he.active = TRUE
                LIMIT 1
            ) new_pic ON TRUE
            WHERE
                task.state = 'open'
                AND (task.company_id != pic.company_id
                     OR pic.working_end_date IS NOT NULL)
            {query_limit}
        """
        self._cr.execute(get_tasklist)
        results = self._cr.dictfetchall()

        if results:
            for res in results:
                task_id = res.get('task_id')
                prev_pic = res.get('prev_pic')
                new_pic = res.get('new_pic')
                new_pic_id = res.get('new_pic_id')
                update_reason = res.get('update_reason')
                task_obj = self.browse(task_id)

                if not new_pic_id:
                    reason_label = "Mutasi" if update_reason == 'mutation' else "Resign"
                    note = (
                        f"Gagal Update PIC: Tidak ditemukan PIC baru "
                        f"untuk task ini. PIC sebelumnya {prev_pic} ({reason_label})."
                    )
                    task_obj.write({'note_delegate': note})
                    continue

                if update_reason == 'mutation':
                    reason_text = f'PIC Sebelumnya Mutasi. {prev_pic} <-> {new_pic}'
                elif update_reason == 'resign':
                    reason_text = f'PIC Sebelumnya Resign. {prev_pic} <-> {new_pic}'
                else:
                    reason_text = f'Update PIC Automatis. {prev_pic} <-> {new_pic}'

                self.env['tw.boom.task.history.user'].create({
                    'employee_id': new_pic_id,
                    'job_id': res.get('new_pic_job_id'),
                    'assign_date': datetime.now(),
                    'company_id': res.get('task_branch'),
                    'task_id': task_id,
                    'reason': reason_text,
                })
                task_obj.write({'employee_id': new_pic_id})

    def _create_boom_task(self, result):
        """
        Create boom tasks from result data with error logging
        
        :param result: list of dict containing task data
        :return: dict with success_count and error_count
        """

        if not result:
            return {'success_count': 0, 'error_count': 0}
        
        success_count = 0
        error_count = 0
        history_model = self.env['tw.boom.task.history'].sudo()

        for data in result:
            no_transaksi = data.get('no_transaksi', 'N/A')
            source_transaksi = data.get('source_transaksi', 'N/A')

            try:
                # Validate model
                model_obj = self.env['ir.model'].sudo().search([
                    ('model', '=', data['model_name'])], limit=1)
                if not model_obj:
                    error_msg = f"Model [{data['model_name']}] tidak ditemukan"
                    history_model.log_error({
                        'no_transaction': no_transaksi,
                        'source_transaction': source_transaksi,
                        'error_message': error_msg,
                        'cron_name': self._name,
                        'method_name': '_create_boom_task',
                    })
                    error_count += 1
                    continue
                
                # Validate category
                category_obj = self.env['tw.boom.category'].sudo().search([
                    ('name', '=', data['kategori'])], limit=1)

                if not category_obj:
                    error_msg = f"Kategori [{data['kategori']}] tidak ditemukan"
                    history_model.log_error({
                        'no_transaction': no_transaksi,
                        'source_transaction': source_transaksi,
                        'error_message': error_msg,
                        'cron_name': self._name,
                        'method_name': '_create_boom_task',
                    })
                    error_count += 1
                    continue
                
                # Validate employee
                company_obj = self.env['res.company'].sudo().search([
                    ('id', '=', data['company_id'])], limit=1)
                
                search_filter_emp = [
                    ('job_id', '=', category_obj.job_id.id),
                    ('company_id', '=', company_obj.id),
                    ('working_end_date', '=', False)
                ]

                employee_obj = self.env['hr.employee'].sudo().search(search_filter_emp, limit=1)
                if not employee_obj:
                    error_msg = f"Employee PIC tidak ditemukan untuk Job ID {category_obj.job_id.name} di {company_obj.name}"
                    
                    history_model.log_error({
                        'no_transaction': no_transaksi,
                        'source_transaction': source_transaksi,
                        'error_message': error_msg,
                        'category_id': category_obj.id,
                        'cron_name': self._name,
                        'method_name': '_create_boom_task',
                    })
                    error_count += 1
                    continue

                # Prepare values
                due_date_teds = data['tgl_due_date_transaksi']
                vals = {
                    'employee_id': employee_obj.id,
                    'job_id': category_obj.job_id.id,
                    'job_delegation_id': category_obj.job_delegation_id.id,
                    'main_category_id': category_obj.main_category_id.id,
                    'sub_category_id': category_obj.sub_category_id.id,
                    'category_id': category_obj.id,
                    'company_id': company_obj.id,
                    'id_transaction': data['transaction_id'],
                    'model_id': model_obj.id,
                    'no_transaction': no_transaksi,
                    'source_transaction': source_transaksi,
                    'transaction_date': data['tgl_transaksi'],
                    'transaction_value': data['value'],
                    'state': data['state'],
                    'due_date': due_date_teds,
                }

                # Optional fields
                optional_fields = ['done_date', 'customer_id', 'finco_id', 'product_id', 'product_color_id', 'lot_id']
                for field in optional_fields:
                    if data.get(field):
                        vals[field] = data[field]

                # Create task
                self.sudo().create(vals)
                
                # Log success
                history_model.log_success({
                    'no_transaction': no_transaksi,
                    'source_transaction': source_transaksi,
                    'category_id': category_obj.id,
                    'cron_name': self._name,
                    'method_name': '_create_boom_task',
                })
                success_count += 1
                
            except Exception as e:
                error_msg = f"Error creating boom task: {str(e)}"
                
                # Log error with full traceback
                history_model.log_error({
                    'no_transaction': no_transaksi,
                    'source_transaction': source_transaksi,
                    'error_message': error_msg,
                    'error_traceback': traceback.format_exc(),
                    'category_id': category_obj.id if 'category_obj' in locals() else False,
                    'cron_name': self._name,
                    'method_name': '_create_boom_task',
                })
                error_count += 1
                continue
        
        # Summary log
        return {
            'success_count': success_count,
            'error_count': error_count
        }
    
