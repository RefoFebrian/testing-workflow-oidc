# 1: imports of python lib
from datetime import datetime, timedelta
import base64
import calendar

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


def _get_range_of_month_or_year(type='month'):
        if type == 'year':
            return [(str(num), str(num)) for num in range(2010, (datetime.now().year)+1)]
        return [(str(idx), str(calendar.month_name[idx])) for idx in range(1, 13)]

class EmployeeSpDigital(models.Model):
    _name = "tw.sp.digital"
    _description = 'SP Digital'
    _order = "id desc"

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string='Name')
    date = fields.Date(string='Date', readonly=True, default=_get_default_date)
    month = fields.Selection(
        _get_range_of_month_or_year(),
        string='Month',
        default=str(datetime.now().month)
    )
    year = fields.Selection(
        _get_range_of_month_or_year(type='year'),
        string='Year',
        default=str(datetime.now().year)
    )
    sp_level = fields.Selection(string='SP', selection=[
        ('1', '1'),
        ('2', '2'),
        ('3', '3')
    ])
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('rfa', 'RFA Deviasi'),
        ('deviasi', 'Deviasi'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], default='draft')
    job_title = fields.Char(string='Job Title', compute="_compute_job_employee", store=True)
    alasan_reject = fields.Text(string='Alasan Reject')
    is_auto_confirm = fields.Boolean(string='Auto Confirmed')
    is_penalty_created = fields.Boolean(string='Pinalti sudah dihitung')
    file_sp = fields.Binary(string='File SP', compute='_compute_file_sp')
    filename_sp = fields.Char(string='File')
    amount_denda = fields.Float(string='Amount')
    total_approval = fields.Float(string='Approval Percentage', compute='_compute_total_approval')

    # Audit Trail
    request_uid = fields.Many2one('res.users', 'Requested by')
    request_date = fields.Datetime('Requested on')
    reject_uid = fields.Many2one('res.users', 'Rejected by')
    reject_date = fields.Datetime('Rejected on')
    confirm_uid = fields.Many2one('res.users', 'Confirmed by')
    confirm_date = fields.Datetime('Confirmed on')
    done_uid = fields.Many2one('res.users', 'Done by')
    done_date = fields.Datetime('Done on')
    received_uid = fields.Many2one('res.users', 'Received (Employee) by')
    received_date = fields.Datetime('Received (Employee) on')
    received_soh_uid = fields.Many2one('res.users', 'Received (Branch Head) by')
    received_soh_date = fields.Datetime('Received (Branch Head) on')

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', domain=[('parent_id','!=',False)])
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    line_ids = fields.One2many(comodel_name='tw.sp.digital.line', inverse_name='sp_digital_id', string='Riwayat Detil SP')
    approval_ids = fields.One2many(comodel_name='tw.approval.line', inverse_name='transaction_id', string='Approval SP', domain=[('model_id','=',_name)])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('filename_sp')
    def _compute_file_sp(self):
        if self.filename_sp:
            image_sp = self.env['tw.config.files'].suspend_security().get_file(self.filename_sp)
            self.file_sp = image_sp
        else : 
            self.file_sp = False

    @api.depends('approval_ids', 'approval_ids.state')
    def _compute_total_approval(self):
        for record in self:
            total = 0.0
            if len(record.approval_ids):
                approved = record.approval_ids.suspend_security().search([
                    ('transaction_id','=',record.id),
                    ('state','=','approve')
                ])
                total = float(len(approved)) / float(len(record.approval_ids))
            record.total_approval = total * 100

    @api.onchange('employee_id', 'company_id')
    def _onchange_employe_id(self):
        if self.company_id:
            query = """
                SELECT hre.id 
                FROM hr_employee hre 
                WHERE hre.company_id = %d
                AND hre.registry_number is not null
                AND hre.working_end_date is null 
            """ % (self.company_id.id)
            self._cr.execute(query)
            ress = self._cr.fetchall()
            ids = [x[0] for x in ress]
            domain ={'employee_id': [('id','in',ids)]}
            return {'domain': domain}

    @api.depends('employee_id')
    def _compute_job_employee(self):
        job_obj = self.employee_id.job_id
        if job_obj:
            self.job_title = job_obj.name
        else:
            self.job_title = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            emp_obj = self.env['hr.employee'].suspend_security().browse(vals['employee_id'])
            vals['name'] = self.env['ir.sequence'].get_sequence_code('SP', emp_obj.company_id.code)

        sp = super(EmployeeSpDigital, self).create(vals_list)
        return sp
    
    def write(self, vals):
        write = super(EmployeeSpDigital, self).write(vals)
        if self.employee_id:
            if vals.get('state') == 'open' or vals.get('line_ids'):
                self.generate_sp_digital_document()
            if vals.get('state') == 'confirmed':
                # Send Notification when state is confirmed
                self._generate_notification('confirmed', 'AND sp.id = %s' % self.id)
                self._create_incentive_penalty()
        
        return write
    
    def unlink(self):
        for x in self:
            if x.state != 'draft':
                raise Warning('Perhatian!\nData tidak bisa dihapus.')
        return super(EmployeeSpDigital, self).unlink()

    # 13: action methods
    def action_sp_digital_tree(self):
        domain = []
        name = 'SP Digital'
        path = 'sp-digital'
        list_view_id = self.env.ref('tw_sp_digital.tw_sp_digital_list_view').id
        form_view_id = self.env.ref('tw_sp_digital.tw_sp_digital_form_view').id
        search_view_id = self.env.ref('tw_sp_digital.tw_sp_digital_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.sp.digital',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_send_to_draft(self):
        self.state = 'draft'

    def send_mail_notification(self, matrix):
        if not matrix:
            raise Warning('Tidak memiliki matrix ! \n tidak dapat kirim notifikasi Email')
        template = self.env.ref('tw_sp_digital.template_mail_for_notification_approval_sp_digital')
        if template:
            mail = self.env['mail.template'].suspend_security().browse(template.id)
            if not mail:
                raise Warning('Mail template is empty')  
        for approval in matrix:
            users = approval.group_id.users
            for user in users:
                # * Check request's branch in user allowed branches
                if self.company_id.id in (user.company_ids.ids):
                    employee_obj = user.employee_id
                    if employee_obj.work_email:                    
                        mail.subject = 'Approval Request'
                        mail.email_to = employee_obj.work_email
                        context = {
                            'email': employee_obj.work_email,
                            'penerima_sp': self.employee_id.name,
                            'nip': self.employee_id.registry_number,
                            'approval_name': employee_obj.name
                        }
                        mail.with_context(context).suspend_security().send_mail(self.id, force_send=True)

    def action_rfa(self):
        if self.state != 'open':
            raise Warning('Hanya bisa Request saat status SP Open.')
        
        # rfa approval matrix
        value = 0
        approval_line = self.env['tw.approval.matrix'].request_by_value(self, value=value)
        if approval_line:
            last_matrix = self.approval_ids.sorted(key=lambda apl: (apl.limit), reverse=True)[0]
            self.suspend_security().send_mail_notification(matrix=last_matrix)

        # Write RFA Data
        self.write({
            'state': 'rfa',
            'request_uid': self.env.user.id,
            'request_date': self._get_default_datetime()
        })

    def action_received(self):
        if self.state != 'confirmed':
            raise Warning('Hanya bisa receive saat status SP Confirm.')
        
        if self.env.user.employee_id.job_id.sales_force_id.value == 'sales_operation_head':
            if self.received_soh_date:
                raise Warning('Anda sudah melakukan konfirmasi')
            else:
                self.write({
                    'state':'done',
                    'received_soh_uid':self.env.user.id,
                    'received_soh_date':self._get_default_datetime()
                })
        elif self.env.user.employee_id.id == self.employee_id.id:
            if self.received_date:
                raise Warning('Anda sudah melakukan konfirmasi')
            else:
                self.write({
                    'state': 'done',
                    'received_uid': self.env.user.id,
                    'received_date': self._get_default_datetime()
                })
        else:
            raise Warning('Hanya karyawan dari SP dan SOH yang dapat melakukan penerimaan SP')
        
        # jika sudah direceived semua
        if self.received_date and self.received_soh_date:
            self.action_done()

    def action_done(self):
        self.write({
            'state': 'done',
            'done_uid': self.env.user.id,
            'done_date': self._get_default_datetime()
        })

    def action_confirm(self, auto_confirm=False):
        if self.state not in ('open', 'rfa'):
            raise Warning('Hanya bisa confirm saat status SP Open.')
        
        self.write({
            'state': 'confirmed',
            'confirm_uid': self.env.user.id,
            'confirm_date': self._get_default_datetime(),
            'is_auto_confirm': auto_confirm
        })

    def action_approve(self):
        if self.state != 'rfa':
            raise Warning('Hanya bisa approve saat status SP RFA.')
        
        approval_sts = self.env['tw.approval.matrix'].approve(self)
        if approval_sts == 1:
            self.write({'state': 'deviasi'})
        elif approval_sts == 0:
            raise Warning('Kamu tidak termasuk group approval')
        
        next_matrix = self.approval_ids.filtered(lambda  apl : apl.state == 'open').sorted(key=lambda apl: (apl.limit), reverse=True)
        if next_matrix:
            self.suspend_security().send_mail_notification(matrix=next_matrix[0])

    def action_reject(self, reject_by_apps=False):
        context = {
            'active_id': self.id,
            'model_name': self._name,
            'update_value': {
                'state': 'confirmed',
                'reject_uid': self._uid,
                'reject_date': self._get_default_datetime()
            }
        }
        if self.state != 'rfa':
            raise Warning('Hanya bisa reject saat status SP RFA.')
        
        if reject_by_apps:
            return self._process_reject(context)

        form_id = self.env.ref('tw_approval.tw_approval_reject_wizard_form_view').id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.approval',
            'name': 'Reject SP Digital',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'target': 'new',
            'context': context
        }
    
    def action_sp_digital_document(self):
        return self.generate_sp_digital_document(True)

    def action_sp_digital_save_document_file(self):
        return self.generate_sp_digital_document(False)
    
    def generate_sp_digital(self):
        query ="""
            SELECT 
                sp.company_id
                , sp.employee_id
                , sp_created.id AS sp_id
                , EXTRACT('month' FROM NOW())::VARCHAR AS month
                , EXTRACT('year' FROM NOW())::VARCHAR AS year
                , array_to_json(
                    array[array_to_json(
                        array['0','0',json_build_object(
                            'sp_level', '1',
                            'type', 'performance',
                            'employee_id', sp.employee_id 
                        )::jsonb]
                    ::json[])]
                ) AS line_ids
            FROM (
                SELECT
                    emp.id AS employee_id
                    , target_line.qty
                    , branch.id AS company_id
                    , COUNT(dsol.id) AS dso
                FROM hr_employee AS emp
                JOIN hr_job AS job ON job.id = emp.job_id
                JOIN res_company AS branch ON branch.id = emp.company_id
                JOIN tw_dealer_sale_order AS dso ON dso.sales_id = emp.id or dso.sales_coordinator_id = emp.id
                JOIN tw_dealer_sale_order_line AS dsol ON dsol.order_id = dso.id
                JOIN tw_sp_digital_target target ON target.company_id = emp.company_id 
                JOIN tw_sp_digital_target_line target_line ON target_line.job_id = emp.job_id and target_line.sp_digital_target_id = target.id
                WHERE 1=1
                    AND job.sales_force_id IS NOT NULL
                    AND job.name ->> 'en_US' NOT IN ('SALES PARTNER', 'Sales Magang', 'Salesman Magang', 'SALES DIGITAL', 'Team Leader Partner')
                    AND emp.working_end_date IS NULL
                    AND (emp.registry_number IS NOT NULL OR emp.identification_id IS NOT NULL)
                    AND EXTRACT(month FROM dso.date_order) = EXTRACT('month' FROM (NOW() - INTERVAL '1 month'))
                    AND EXTRACT(years FROM dso.date_order) = EXTRACT('year' FROM (NOW() - INTERVAL '1 month'))
                GROUP BY emp.id, job.id, target_line.id, branch.id
            ) AS sp
            LEFT JOIN tw_sp_digital AS sp_created ON sp_created.employee_id = sp.employee_id
                AND sp_created.month = EXTRACT('month' FROM NOW())::VARCHAR
                AND sp_created.year = EXTRACT('year' FROM NOW())::VARCHAR
            WHERE sp.qty > sp.dso
        """
        self._cr.execute (query)
        ress = self._cr.dictfetchall()
        if ress:
            for res in ress:
                sp_id = res.pop('sp_id')
                # IF any SP created for this month
                if sp_id:
                    sp_line_data = {
                        'type': 'performance',
                        'sp_level': '1',
                        'employee_id': res.get('employee_id'),
                        'sp_digital_id': sp_id,
                    }
                    self.env['tw.sp.digital.line'].sudo().create(sp_line_data)
                else:
                    self.env['tw.sp.digital'].sudo().create(res)

    def generate_sp_final(self):
        # Search Active SP
        query = """
            SELECT		
                emp.id AS employee_id
                , emp.name AS employee_name
                , sp.id AS sp_id
                , json_agg(DISTINCT JSON_BUILD_OBJECT(
                    'id', previous_sp.id,
                    'name', previous_sp.name,
                    'sp_level', previous_sp.sp_level,
                    'employee_id', previous_sp.employee_id
                )::JSONB) AS previous_sp
                , MAX(previous_sp.sp_level) AS previous_sp_level
                , CASE WHEN MAX(previous_sp.id) IS NOT NULL
                        THEN
                        	CASE WHEN (MAX(previous_sp.sp_level)::int) <= MAX(spl.sp_level)::int
                                AND MAX(spl.sp_level)::int < 3
                            	THEN (MAX(previous_sp.sp_level)::int + 1)::varchar
                            ELSE '3'
                        END
                    ELSE (MAX(spl.sp_level))
                END AS sp_level
                , (
                    SELECT
                        COALESCE(SUM(incentive_value),0)
                    FROM tw_employee_incentive
                    WHERE employee_id = emp.id
                    AND date BETWEEN (date_trunc('month', sp.date::date) - interval '1 month')::date 
                    AND (date_trunc('month', sp.date::date) - interval '1 day')::date
                    AND model_name = 'tw.dealer.sale.order'
                    AND state = 'earned'
                ) AS incentive
            FROM tw_sp_digital AS sp
            JOIN tw_sp_digital_line AS spl ON spl.sp_digital_id = sp.id
            JOIN hr_employee emp ON emp.id = sp.employee_id
            LEFT JOIN tw_sp_digital AS previous_sp ON previous_sp.employee_id = emp.id
            	AND previous_sp.state != 'draft'
            	AND (previous_sp.year || '-' || previous_sp.month || '-01')::date > TO_CHAR(NOW() - '6 month'::interval, 'yyyy-mm-01')::date
            WHERE 1=1
            AND sp.state = 'draft'
            AND sp.month = extract('month'from NOW())::varchar
            AND sp.year = extract('year'from NOW())::varchar
            GROUP BY emp.id, sp.id
        """
        self._cr.execute (query)
        ress = self._cr.dictfetchall()
        if ress:
            # Loop and write SP 
            # also give info about previous SP & denda in detail
            to_create_previous_sp = []
            for data in ress:
                sp = self.env['tw.sp.digital'].sudo().browse(data.get('sp_id'))
                
                # Denda
                tingkat_denda = [0, 25, 50, 100] # dalam persen (%)
                sp_level = data.get('sp_level')
                amount_denda = data.get('incentive') * (tingkat_denda[int(sp_level)] / 100)
                
                sp.sudo().write({
                    'state': 'open',
                    'amount_denda': amount_denda,
                    'sp_level': sp_level
                })
                if data.get('previous_sp'):
                    for ps in data.get('previous_sp'):
                        if ps.get('id', False):
                            to_create_previous_sp.append({
                                'name': ps.get('name'),
                                'type': 'previous_sp',
                                'sp_level': ps.get('sp_level'),
                                'employee_id': ps.get('employee_id'),
                                'sp_digital_id': data.get('sp_id'),
                            })

            # Create if there is any previous SP that make SP level increase
            if to_create_previous_sp:
                created_sp = self.env['tw.sp.digital.line'].sudo().create(to_create_previous_sp)

    def generate_sp_digital_document(self, action=False):
        self.ensure_one()
        datas = {
             'id': self.id,
             'model': 'tw.sp.digital',
             'data': self.read()[0],
        }
        # Retrieve pdf file and save it to fields if its not from action
        if not action:
            report = self.env['ir.actions.report']._render_qweb_pdf('tw_sp_digital.action_sp_digital_pdf_report', data=datas)
            b64_pdf = base64.b64encode(report[0])
            filename_sp = 'tw_sp_digital' + '-dokumen_sp-' + str(self.employee_id.name).lower() + '-' + str(self.id) + '.pdf'
            self.env['tw.config.files'].suspend_security().upload_file(filename_sp, b64_pdf)
            self.filename_sp = filename_sp
        else:
            # generate report if else
            report = self.env.ref('tw_sp_digital.action_sp_digital_pdf_report').report_action(self, data=datas)
            return report
        
    def generate_sp_active(self):
        date = datetime.today().day
        # This used for activate SP after not being confirmed or approved on 9th every month
        param_date_not_confirm = self.env['ir.config_parameter'].get_param('tw_sp_digital_param_date_not_confirm')
        if date >= int(param_date_not_confirm):
            open_sp = self.env['tw.sp.digital'].suspend_security().search([
                ('state','in',('open','rfa'))
            ], limit=10)
            if open_sp:
                for sp in open_sp:
                    sp.action_confirm(True)

    def generate_notification_open(self):
        self._generate_notification('open')

    def generate_notification_confirmed(self):
        self._generate_notification('confirmed', "AND sp.state = 'confirmed'")

    def content_notification_wa(self, ress, state):
        to_create_wa_outbox = []
        # Search config and model
        api_config_wa_obj = self.env['tw.api.configuration'].get_api_config('Whatsapp')
        if not api_config_wa_obj:
            raise Warning('Attention, No Configuration for Whatsapp is Active!')
        model_obj = self.env['ir.model'].suspend_security().search([
            ('model','=','tw.sp.digital')
        ], limit=1)
        
        if state == 'open':
            for data in ress:
                content_msg = '' #? Put the data inside message
                content_msg = """
                    Kepada Yth. {nama_kacab},
                    sehubungan dengan karyawan anda yang bernama :
                """.format(nama_kacab=(data.get('name')) + content_msg) #? Create Header Message
                
                for sp_data in data.get('sp_data'):
                    content_msg += """
                        Nama Karyawan : {nama_karyawan}
                        NIK : {nik}
                        Jabatan : {jabatan_karyawan}
                        Cabang : {cabang_karyawan}
                        Akan mendapatkan Surat Peringatan {sp_level},
                    """.format(
                        nama_karyawan=sp_data.get('name'),
                        nik=sp_data.get('nik'),
                        jabatan_karyawan=sp_data.get('job'),
                        cabang_karyawan=sp_data.get('branch'),
                        sp_level=sp_data.get('sp_level')
                    )
                
                content_msg += """
                    Mohon segera konfirmasi terkait Surat Peringatan ini melalui Aplikasi doodool atau Situs Web Tunas Honda.
                    Atas Perhatian anda kami ucapkan terimakasih. Salam Satu Hati.
                """
                to_create_wa_outbox = self.create_wa_outbox(to_create_wa_outbox, data, content_msg, api_config_wa_obj, model_obj) #? Create Outbox Message to KaCab
        else:
            for data in ress:
                content_msg = '' #? Put the data inside message
                content_msg = """
                    Kepada Yth. {nama_kacab},
                    sehubungan dengan karyawan anda yang bernama :
                """.format(nama_kacab=(data.get('name')) + content_msg) #? Create Header Message
                
                for sp_data in data.get('sp_data'):
                    content_msg_employee = self.employee_content_notification_wa(sp_data) #? Create Content Message to Employee
                    to_create_wa_outbox = self.create_wa_outbox(to_create_wa_outbox, sp_data, content_msg_employee, api_config_wa_obj, model_obj) #? Append Employee to Outbox Message
                    
                    content_msg += """
                        Nama Karyawan : {nama_karyawan}
                        NIK : {nik}
                        Jabatan : {jabatan_karyawan}
                        Cabang : {cabang_karyawan}
                        Telah mendapatkan Surat Peringatan {sp_level},
                    """.format(
                        nama_karyawan=sp_data.get('name'),
                        nik=sp_data.get('nik'),
                        jabatan_karyawan=sp_data.get('job'),
                        cabang_karyawan=sp_data.get('branch'),
                        sp_level=sp_data.get('sp_level')
                    )
                
                content_msg += """
                    Atas Perhatian anda kami ucapkan terimakasih. Salam Satu Hati.
                """
                to_create_wa_outbox = self.create_wa_outbox(to_create_wa_outbox, data, content_msg, api_config_wa_obj, model_obj) #? Create Outbox Message to KaCab
                
        return to_create_wa_outbox, api_config_wa_obj
    
    def employee_content_notification_wa(self, data):
        content_msg = '' #? Put the data inside message
        content_msg += """
            Kepada Yth. {nama_karyawan},
            anda telah mendapatkan surat peringatan {sp_level}.
            Silahkan konfirmasi tanda terima melalui Aplikasi doodool atau Situs Web Tunas Honda.
            Atas Perhatian anda kami ucapkan terimakasih. Salam Satu Hati.
        """.format(nama_karyawan=(data.get('name')), sp_level=(data.get('sp_level'))) #? Create Employee Message
        
        return content_msg
    
    def create_wa_outbox(self, to_create_wa_outbox, data, content_msg, config, model_obj): #? Append all Outbox into to_create_wa_outbox
        if config and model_obj and data.get('phone_number'):
            to_create_wa_outbox.append({
                'company_id': data.get('company_id'),
                'name': str(data.get('name')).strip().upper(),
                'phone_number': data.get('phone_number'),
                'message': content_msg,
                'transaction_id': self.id,
                'model_id': model_obj.id,
                'model_name': model_obj.model
            }) #? Update new value in to_create_wa_outbox
        
        return to_create_wa_outbox

    # 14: private methods
    def _check_user_groups(self):
        # Search Open approval and order it by limit
        approvals_obj = self.approval_ids.search([
            ('transaction_id','=',self.id),
            ('model_id.model','=',self._name),
            ('state','=','open'),
        ], order='limit')

        # Check if user has group, end the loop & write approve line if user has it
        for approval in approvals_obj:
            # User can has more than 1 allowed group
            # Check if the user already approving this transaction
            user_approval_obj = self.approval_ids.search([
                ('transaction_id','=',self.id),
                ('model_id.model','=',self._name),
                ('approver_id','=',self.env.user.id),
            ])
            if self.env.user.has_group(approval.group_id.get_external_id().get(approval.group_id.id)) and not user_approval_obj:
                return approval

        # If none of the approvals match the user groups, raise warning.
        raise Warning("Anda 'Tidak Dapat' atau 'Sudah' melakukan Approval. \nPeriksa Tab Approval.")
    
    def _generate_notification(self, state, additional_where_clause=False):
        if not additional_where_clause:
            additional_where_clause = """
                AND sp.state = 'open'
                AND sp.month = EXTRACT('month'FROM NOW())::VARCHAR
                AND sp.year = EXTRACT('year'FROM NOW())::VARCHAR
            """
        
        # Search Open SP
        query = """
            SELECT 
                sp.id AS sp_id
                , branch.id AS company_id
                , kacab.id
                , kacab.name
                , kacab.work_email
                , COALESCE(kacab.mobile_phone, kacab.work_phone) AS phone_number
                , JSON_AGG(JSON_BUILD_OBJECT(
                    'id', emp.id,
                    'nik', emp.registry_number,
                    'name', emp.name,
                    'company_id', branch.id,
                    'company', branch.name,
                    'job', job.name ->> 'en_US',
                    'phone_number', COALESCE(emp.mobile_phone, emp.work_phone),
                    'work_email', emp.work_email,
                    'sp_level', sp.sp_level
                )::JSONB) AS sp_data
            FROM tw_sp_digital AS sp
            JOIN res_company AS branch ON branch.id = sp.company_id
            JOIN hr_employee AS emp ON emp.id = sp.employee_id
            JOIN hr_job AS job ON job.id = emp.job_id
            LEFT JOIN tw_branch_setting AS branch_setting ON branch_setting.id = branch.branch_setting_id
            JOIN hr_employee AS kacab ON kacab.id = branch_setting.branch_head_id
            WHERE 1=1
            {additional_where_clause}
            GROUP BY sp.id, kacab.id, branch.id
        """.format(additional_where_clause = additional_where_clause)
        self._cr.execute (query)
        ress = self._cr.dictfetchall()
        if ress:
            # WA
            # ? turned off temporary
            # to_create_wa_outbox, config = self.content_notification_wa(ress, state)
            # # Create if there is Open SP that need to notif KaCab
            # if to_create_wa_outbox:
            #     #Create WA Outbox
            #     outbox_created = self.env['tw.wa.outbox'].suspend_security().create(to_create_wa_outbox)
            #     for x in outbox_created: #? using looping to avoid singleton
            #         response = x.action_send(config)
            
            # Firebase
            to_create_notification_firebase = self._get_notification_firebase_content(ress, state)
            if to_create_notification_firebase:
                create_message_data= self.env['tw.firebase.notification'].sudo().create(to_create_notification_firebase)
                if create_message_data :
                    for message in create_message_data:
                        message_title = 'Notifikasi Surat Peringatan kepada ' + (message.customer_name or '')
                        message_body  = 'Mohon segera konfirmasi terkait Surat Peringatan ini melalui Aplikasi doodool atau Situs Web Tunas Honda.'
                        data = {
                            'priority': 'normal',
                            'notification': {
                                'id': message.id,
                                'body': '%s' % (message_body),
                                'title': '%s' % (message_title),
                                'icon': 'logo_sahabat_tunas',
                                'model': 'tw.firebase.notification',
                                'click_action': 'com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications'
                            },
                            'data': {
                                'text': 'new Symulti update !'
                            }
                        }
                        obj_firebase_user = self.env['tw.firebase.user'].search([
                            ('user_id','=',message.employee_receiver_id.user_id.id),
                            ('active','=',True)
                        ])
                        if obj_firebase_user:
                            for token in obj_firebase_user:
                                try:
                                    obj_firebase_user.notify_single_device(token.firebase_token, data)
                                    message.write({'send_date': self._get_default_date(), 'state': 'unread'})
                                except Exception as e:
                                    _logger.error(e)

            # Email
            to_create_notification_email = self._get_notification_email_content(ress, state)
            if to_create_notification_email:
                self.suspend_security()._send_notification(data=to_create_notification_email)

    def _create_incentive_penalty(self):
        if self.amount_denda > 0:
            now = datetime.now()
            job_id = self.employee_id.get_job_by_date(now)
            self.env['tw.employee.incentive'].suspend_security().create({
                'company_id': self.company_id.id,
                'type': 'sale',
                'date': self._get_default_date(),
                'earned_date': self._get_default_date(),
                'state': 'earned',
                'model_name': 'tw.sp.digital',
                'transaction_id': self.name,
                'incentive_value': self.amount_denda * -1,
                'employee_id': self.employee_id.id,
                'job_id': job_id.id
            })

        self.is_penalty_created = True

    def _get_notification_firebase_content(self, ress, state):
        to_create_notification_firebase = []
        # Send to branch head only
        if state == 'open':
            model_category = self.env['tw.firebase.notification.category'].suspend_security().search([
                ('name','=','Notification SP Open Kacab')
            ], limit=1)
            template = model_category.content_template_id
            if template:
                for data in ress:
                    left_content_msg = '' #? Put the data left side message
                    right_content_msg = '' #? Put the data right side message
                    for sp_data in data.get('sp_data'):
                        left_content_msg += """
                            <br/>Nama Karyawan<br/>NIK<br/>Jabatan<br/>Cabang<br/>Akan mendapatkan Surat Peringatan (SP {sp_level})<br/>
                        """.format(sp_level=sp_data.get('sp_level'))
                        right_content_msg += """
                            <br/>: {nama_karyawan}<br/>: {nik}<br/>: {jabatan_karyawan}<br/>: {cabang_karyawan}<br/><br/>
                        """.format(
                            nama_karyawan=sp_data.get('name'),
                            nik=sp_data.get('nik'),
                            jabatan_karyawan=sp_data.get('job'),
                            cabang_karyawan=sp_data.get('branch')
                        )
                    content_msg = template.content
                    content_msg = content_msg.replace('%name%', data.get('name'))
                    content_msg = content_msg.replace('%left%', left_content_msg)
                    content_msg = content_msg.replace('%right%', right_content_msg)
                    to_create_notification_firebase = self._append_to_create_firebase_notification_data(to_create_notification_firebase, data, content_msg, model_category) #? Create Outbox Message to KaCab
        else:
            # Send to branch head & Employee only
            model_category_kacab = self.env['tw.firebase.notification.category'].suspend_security().search([
                ('name','=','Notification SP Confirmed Kacab')
            ], limit=1)
            template_for_kacab = model_category_kacab.content_template_id
            model_category_employee = self.env['tw.firebase.notification.category'].suspend_security().search([
                ('name','=','Notification SP Employee')
            ], limit=1)
            template_for_employee = model_category_employee.content_template_id
            # Insert notification text 
            for data in ress:
                left_content_msg = '' #? Put the data left side message
                right_content_msg = '' #? Put the data right side message
                for sp_data in data.get('sp_data'):
                    left_content_msg += """
                        <br/>Nama Karyawan<br/>NIK<br/>Jabatan<br/>Cabang<br/><br/>
                    """.format(sp_level=sp_data.get('sp_level'))
                    right_content_msg += """
                        <br/>: {nama_karyawan}<br/>: {nik}<br/>: {jabatan_karyawan}<br/>: {cabang_karyawan}<br/><br/>
                    """.format(
                        nama_karyawan=sp_data.get('name'),
                        nik=sp_data.get('nik'),
                        jabatan_karyawan=sp_data.get('job'),
                        cabang_karyawan=sp_data.get('branch')
                    )
                    if template_for_employee:
                        content_msg_employee = template_for_employee.content
                        content_msg_employee = content_msg_employee.replace('%name%', sp_data.get('name'))
                        content_msg_employee = content_msg_employee.replace('%sp_level%', sp_data.get('sp_level'))
                        to_create_notification_firebase = self._append_to_create_firebase_notification_data(to_create_notification_firebase, sp_data, content_msg_employee, model_category_employee) #? Create Outbox Message to Employee
                if template_for_kacab:
                    content_msg = template_for_kacab.content
                    content_msg = content_msg.replace('%name%', data.get('name'))
                    content_msg = content_msg.replace('%left%', left_content_msg)
                    content_msg = content_msg.replace('%right%', right_content_msg)
                    to_create_notification_firebase = self._append_to_create_firebase_notification_data(to_create_notification_firebase, data, content_msg, model_category_kacab) #? Create Outbox Message to KaCab
        
        return to_create_notification_firebase
    
    def _get_notification_email_content(self, ress, state):
        to_create_notification_email = []
        # Send to Branch Head Only
        template_email_sp_digital = self.env.ref('tw_sp_digital.template_mail_for_kacab_open_sp_digital').id
        if state == 'open':
            table_line = []
            for data in ress:
                name = data.get('name','')
                for sp_data in data.get('sp_data'):
                    table_line.append({
                        'nama_karyawan': sp_data.get('name'),
                        'nik': sp_data.get('nik'),
                        'jabatan_karyawan': sp_data.get('job'),
                        'cabang_karyawan': sp_data.get('branch'),
                        'sp_level': sp_data.get('sp_level')
                    })

                to_create_notification_email.append({
                    'id': data.get('sp_id'),
                    'name': name,
                    'status': 'kacab_open',
                    'email_kacab': data.get('work_email',None),
                    'template_email': template_email_sp_digital.id,
                    'employees': table_line
                })
        else:
            # Send to Branch Head & Employee only
            send_mails = []
            for data in ress:
                name = data.get('name', '')
                table_line = []
                for sp_data in data.get('sp_data'):
                    send_mails.append(sp_data.get('work_email'))
                    table_line.append({
                        'nama_karyawan': sp_data.get('name'),
                        'nik': sp_data.get('nik'),
                        'jabatan_karyawan': sp_data.get('job'),
                        'cabang_karyawan': sp_data.get('branch'),
                        'sp_level': sp_data.get('sp_level')
                    })

                to_create_notification_email.append({
                    'id': data.get('sp_id'),
                    'template_email': template_email_sp_digital,
                    'name': name,
                    'status': 'kacab_and_employee',
                    'employees': table_line,
                    'email_kacab': data.get('work_email'),
                    'email': send_mails
                })

        return to_create_notification_email
    
    # TODO: wait for firebase module
    def _append_to_create_firebase_notification_data(self, to_create_notification_firebase, data, content_msg, template): #? Append all Outbox into to_create_notification_firebase
        to_create_notification_firebase.append({
            'name': template.name + '[' + str(data.get('id')) + '-' + str(data.get('company_id')) + ']',
            'customer_name': data.get('name'),
            'message': content_msg,
            'company_id': data.get('company_id'),
            'employee_receiver_id': data.get('id'),
            'category_id': template.id,
        })
        
        return to_create_notification_firebase
    
    def _send_notification(self, data, type=None):
        for email_data in data:
            send_mail = email_data['email']
            status = email_data.get('status', None)
            template_email = email_data.get('template_email', None)
            
            try:
                sp_digital_obj = self.suspend_security().browse(email_data.get('id'))
                mail = self.env['mail.template'].suspend_security().browse(template_email)
                # Send to Branch Head Only
                if status == 'kacab_open':
                    email_data['email'] = email_data['email_kacab']
                    mail.with_context(email_data).suspend_security().send_mail(sp_digital_obj.id, force_send=True)
                
                # Send to Branch Head & Employee only
                if status == 'kacab_and_employee':
                    if 'email_kacab' in email_data:
                        email_data['status'] = 'kacab_confirmed'
                        email_data['email'] = email_data['email_kacab']
                        email_values = {
                            'email_to': email_data['email_kacab'],
                        }
                        mail.with_context(email_data).suspend_security().send_mail(sp_digital_obj.id, force_send=True, email_values=email_values)
                    
                    for email_to_send in send_mail:
                        email_data['status'] = 'employee'
                        email_data['email'] = email_to_send
                        mail.with_context(email_data).suspend_security().send_mail(sp_digital_obj.id, force_send=True)
            
            except Exception as e:
                _logger.error(e)

    def _process_reject(self, ctx):
        approval_obj = self.env['tw.approval'].suspend_security().with_context(ctx).create({'reason': self._context.get('reason')})
        return approval_obj.action_approval_reject()