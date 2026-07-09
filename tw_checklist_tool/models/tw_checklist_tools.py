# 1: imports of python lib
import calendar
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, api, _, fields
from odoo.exceptions import UserError
from odoo.tools.translate import _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwChecklistTools(models.Model):
    _name = "tw.checklist.tools"
    _description = "Checklist Tool"
    _order = "create_date DESC"

    # 7: defaults methods
    @api.model
    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.user.company_ids
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False

    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    def _get_year(self):
        return date.today().year
    
    def get_month_selection(self):
        return [(str(i), _(calendar.month_name[i])) for i in range(1, 13)]

    def get_weeks_in_month(self, month, year):
        month = int(month)
        year = int(year)

        cal = calendar.Calendar(firstweekday=calendar.MONDAY)
        weeks = cal.monthdatescalendar(year, month)

        filtered_weeks = [week for week in weeks if any(day.month == month for day in week)]
        return len(filtered_weeks)

    # 8: fields
    name = fields.Char('Name', compute='_compute_name', store=True, index=True, readonly=True)
    tahun = fields.Char('Tahun', default=_get_year)
    category_name = fields.Char(related='category_master_tool_id.name', string='Category Name')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    posted_date = fields.Datetime('Done on')
    confirm_date = fields.Datetime('Open on')
    state = fields.Selection([('draft','Draft'),('open','Open'),('RFA','Request for Approval'),('approve','Approved'),('done','Done')], default='draft')
    division = fields.Selection([('Sparepart','Sparepart')],default='Sparepart')
    periode_bulan = fields.Selection(selection=get_month_selection, string='Month')
    
    # 9: relation fields
    confirm_uid = fields.Many2one('res.users', string="Open by")
    posted_uid = fields.Many2one('res.users', string="Done by")
    company_id = fields.Many2one('res.company', string="Branch")
    pic_id = fields.Many2one('hr.employee', string="PIC")
    category_master_tool_id = fields.Many2one('tw.selection', "Category", domain=[('type', '=', 'MasterToolCategory')])
    line_ids = fields.One2many('tw.checklist.tools.line', 'checklist_id', 'Order Lines')
    
    # 10: constraints & sql constraints
    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for record in self:
            if record.start_date and record.end_date:
                start_date = datetime.strptime(str(record.start_date), '%Y-%m-%d').date()
                end_date = datetime.strptime(str(record.end_date), '%Y-%m-%d').date()
                
                current_date = datetime.now().date()
                current_month = current_date.month
                current_year = current_date.year

                if record.start_date and record.end_date:
                    start_month = start_date.month
                    end_month = end_date.month
                    start_year = start_date.year
                    end_year = end_date.year

                    if start_date > end_date:
                        raise UserError(_("Start date tidak boleh lebih besar dari end date."))
                    if start_year != end_year or start_month != end_month:
                        raise UserError(_("Start date dan end date harus berada di bulan yang sama."))
                    
                    if start_month != current_month or start_year != current_year:
                        raise UserError(_("Start date harus berada di bulan saat ini."))
                    if end_month != current_month or end_year != current_year:
                        raise UserError(_("End date harus berada di bulan saat ini."))

                    ranged_date = (end_date - start_date).days
                    days_in_month = (end_date.replace(day=1) + relativedelta(months=1, days=-1)).day
                    if ranged_date > days_in_month:
                        raise UserError(_("Rentang waktu maksimal adalah 1 bulan."))

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.company_id:
                rec.name = False
                continue

            sequence_code = 'CT'
            branch_code = rec.company_id.code or ''

            seq_date = None
            if rec.start_date:
                seq_date = rec.start_date
            elif rec.periode_bulan and rec.tahun:
                try:
                    year = int(rec.tahun)
                    month = int(rec.periode_bulan)
                    seq_date = date(year, month, 1)
                except ValueError:
                    pass

            generated_name = rec.env['ir.sequence'].get_sequence_code(sequence_code, branch_code, sequence_date=seq_date)
            rec.name = generated_name

    @api.onchange('company_id')
    def onchange_employee(self):
        self.pic_id = False
        ids = []
        if self.company_id:
            jobs = self.env['hr.job'].suspend_security().search(
                [('name', 'in', ('MECHANIC', 'MEKANIK MITRA', 'PARTMAN', 'FRONT DESK',
                                 'FRONT DESK (PARTMAN)', 'MECHANIC HEAD', 'SERVICE ADVISOR',
                                 'WORKSHOP HEAD'))])
            empl = self.env['hr.employee'].sudo().search([
                ('company_id', '=', self.company_id.id),
                ('job_id', 'in', [j.id for j in jobs]),
                ('working_end_date', '=', False), ('active', '=', True)])
            ids = [e.id for e in empl]
        domain = {'pic_id': [('id', 'in', ids)]}
        return {'domain': domain}

    @api.onchange('category_master_tool_id')
    def _onchange_category_periode(self):
        self.start_date = False
        self.end_date = False
        self.periode_bulan = False

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
            current_date = datetime.now().date()
            selected_date = datetime.strptime(str(self.start_date), '%Y-%m-%d').date()
            if selected_date.month != current_date.month or selected_date.year != current_date.year:
                self.start_date = False
                return {
                    'warning': {
                        'title': _("Peringatan!"),
                        'message': _("Anda hanya bisa memilih tanggal di bulan saat ini.")
                    }
                }

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date:
            current_date = datetime.now().date()
            selected_date = datetime.strptime(str(self.end_date), '%Y-%m-%d').date()
            if selected_date.month != current_date.month or selected_date.year != current_date.year:
                self.end_date = False
                return {
                    'warning': {
                        'title': _("Peringatan!"),
                        'message': _("Anda hanya bisa memilih tanggal di bulan saat ini.")
                    }
                }

    @api.onchange('periode_bulan')
    def _onchange_periode_bulan(self):
        if self.periode_bulan:
            current_month = datetime.now().month
            selected_month = int(self.periode_bulan)

            if selected_month != current_month:
                self.periode_bulan = False
                return {
                    'warning': {
                        'title': _("Peringatan!"),
                        'message': _("Anda hanya bisa memilih bulan saat ini.")
                    }
                }

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get('company_id')
            pic_id = vals.get('pic_id')
            category_master_tool = vals.get('category_master_tool_id')
            start_date = vals.get('start_date')
            end_date = vals.get('end_date')
            tahun = self._get_year()
            periode_bulan = vals.get('periode_bulan')

            empl = self.env['hr.employee'].sudo().search([('id', '=', pic_id)])

            if self._is_previous_transaction_done(company_id, pic_id, category_master_tool):
                raise UserError(_(
                    "Perhatian!\nChecklist Tool tidak dapat dibuat untuk PIC %s\nkarena transaksi sebelumnya untuk pic tersebut belum selesai (State Done)." % (
                        empl.name)))

            domain_entries = [
                ('company_id', '=', company_id),
                ('pic_id', '=', pic_id),
                ('category_master_tool_id', '=', category_master_tool)
            ]
            if start_date and end_date:
                domain_entries += [
                    ('start_date', '<=', end_date),
                    ('end_date', '>=', start_date)
                ]
            else:
                domain_entries += [
                    ('periode_bulan', '=', periode_bulan),
                    ('tahun', '=', tahun)
                ]
            existing_entries = self.search(domain_entries)
            if existing_entries:
                raise UserError(_(
                    "Perhatian! Terdapat periode tanggal/bulan yang sudah terbuat. Silakan pilih tanggal/bulan yang berbeda."))

        checklist = super(TwChecklistTools, self.sudo()).create(vals_list)

        return checklist

    def write(self, vals):
        company_id = vals.get('company_id', self.company_id.id)
        pic_id = vals.get('pic_id', self.pic_id.id)
        category_master_tool_id = vals.get('category_master_tool_id', self.category_master_tool_id.id)
        tahun = vals.get('tahun', self.tahun)
        start_date = vals.get('start_date', self.start_date)
        end_date = vals.get('end_date', self.end_date)
        periode_bulan = ('periode_bulan', self.periode_bulan)

        empl = self.env['hr.employee'].sudo().search([('id', '=', vals.get('pic_id'))])

        if vals.get('pic_id') and vals.get('pic_id') != self.pic_id.id:
            if self._is_previous_transaction_done(company_id, vals.get('pic_id'), category_master_tool_id):
                raise UserError(_(
                    "Perhatian!\nChecklist Tool tidak dapat diubah untuk PIC %s\nkarena checklist sebelumnya untuk pic tersebut belum selesai (State Done)." % (
                        empl.name)))

        domain_entries = [
            ('company_id', '=', company_id),
            ('pic_id', '=', pic_id),
            ('category_master_tool_id', '=', category_master_tool_id)
        ]

        if start_date and end_date:
            domain_entries += [
                ('start_date', '<=', end_date),
                ('end_date', '>=', start_date),
                ('id', '!=', self.id)
            ]
        else:
            domain_entries += [
                ('periode_bulan', '=', periode_bulan),
                ('tahun', '=', tahun),
                ('id', '!=', self.id)
            ]
        existing_entries = self.search(domain_entries)
        if existing_entries:
            raise UserError(_(
                "Perhatian! Terdapat periode tanggal/bulan yang sudah terbuat. Silakan pilih tanggal/bulan yang berbeda."))

        result = super(TwChecklistTools, self).write(vals)
        return result
    
    def unlink(self):
        if self:
            raise UserError(_('Perhatian! Checklist Tool tidak bisa dihapus!'))
        return super(TwChecklistTools, self).unlink()

    # 13: action methods
    def action_done(self, confirmed=False):
        if not confirmed:
            tool_not_checked = False
            today = datetime.today().date()
            for line in self.line_ids:
                if line.date:
                    line_date = line.date
                    if today < line_date:
                        raise UserError(_("Perhatian!\nBelum bisa melakukan Done karena periode belum mencapai akhir periode."))

                if line.week and line.week != '4':
                    raise UserError(_(
                        "Perhatian!\nBelum bisa melakukan Done karena periode belum mencapai akhir periode. (minggu ke-4)."))

                for detail_line in line.checklist_detail_ids:
                    if not detail_line.tools_state:
                        tool_not_checked = True
                        break

            if tool_not_checked:
                return {
                    'name': 'Konfirmasi Done',
                    'type': 'ir.actions.act_window',
                    'res_model': 'tw.upload.message.wizard',
                    'view_mode': 'form',
                    'view_id': self.env.ref('tw_checklist_tool.view_tw_import_result_message_wizard').id,
                    'target': 'new',
                    'context': {
                        'message': "Perhatian!\nTerdapat tools yang belum di cek kondisinya pada salah satu periode. Apakah Anda yakin ingin melakukan Done?",
                        'default_parent_id': self.id,
                        'method_to_call': 'action_done',
                    }
                }
        
        self.write({
            'state': 'done',
            'posted_uid': self._uid,
            'posted_date': datetime.now()
        })

    def action_generate_line(self):
        for checklist in self:
            category_obj = self.env['tw.selection'].suspend_security().search([
                ('id', '=', checklist.category_master_tool_id.id),
                ('type', '=', 'MasterToolCategory')
            ])

            should_generate = True
            if checklist.line_ids:
                if category_obj.name != 'Special Tools':
                    dates = sorted([l.date for l in checklist.line_ids if l.date])
                    if dates:
                        start_date_check = checklist.start_date
                        end_date_check = checklist.end_date
                        if isinstance(start_date_check, str):
                            start_date_check = datetime.strptime(start_date_check, '%Y-%m-%d').date()
                        if isinstance(end_date_check, str):
                            end_date_check = datetime.strptime(end_date_check, '%Y-%m-%d').date()

                        if dates[0] == start_date_check and dates[-1] == end_date_check:
                            should_generate = False
                else:
                    if checklist.line_ids[0].periode_bulan == checklist.periode_bulan and checklist.line_ids[0].tahun == checklist.tahun:
                        should_generate = False

            if not should_generate:
                if checklist.state == 'draft':
                    checklist.write({
                        'state': 'open',
                        'confirm_uid': self._uid,
                        'confirm_date': datetime.now()
                    })
                continue

            if checklist.line_ids:
                checklist.line_ids.unlink()

            company_id = checklist.company_id.id
            pic_id = checklist.pic_id.id
            category_master_tool_id = checklist.category_master_tool_id.id
            start_date = checklist.start_date
            end_date = checklist.end_date
            periode_bulan = checklist.periode_bulan
            tahun = checklist.tahun

            master_tools_obj = self.env['tw.master.tools'].suspend_security().search([
                ('company_id', '=', company_id),
                ('pic_id', '=', pic_id),
                ('category_master_tool_id', '=', category_master_tool_id),
            ])
            master_tools_line_obj = master_tools_obj.tw_master_tools_line_ids
            if not master_tools_obj or not master_tools_line_obj:
                raise UserError(_(
                    "Perhatian!\nMaster Tools untuk Branch %s PIC Mekanik %s belum ada atau tidak memiliki detail tools." % (
                        checklist.company_id.name, checklist.pic_id.name)))

            detail_lines_data = []
            if category_obj.name != 'Special Tools':
                # DAILY
                current_date = datetime.strptime(str(start_date), '%Y-%m-%d').date()
                end_date = datetime.strptime(str(end_date), '%Y-%m-%d').date()

                while current_date <= end_date:
                    daily_lines = []
                    for tool in master_tools_line_obj:
                        daily_lines.append((0, 0, {
                            'master_tool_id': master_tools_obj.id,
                            'master_tool_line_id': tool.id,
                            'filename': tool.filename,
                            'product_id': tool.product_id.id,
                            'location_id': master_tools_obj.location_id.id,
                        }))
                    detail_lines_data.append((0, 0, {
                        'date': current_date,
                        'checklist_detail_ids': daily_lines
                    }))
                    current_date += timedelta(days=1)
            else:
                # WEEKLY
                month_now = periode_bulan
                year_now = tahun
                weeks = 1
                while weeks <= 4:
                    weekly_lines = []
                    for tool in master_tools_line_obj:
                        weekly_lines.append((0, 0, {
                            'master_tool_id': master_tools_obj.id,
                            'master_tool_line_id': tool.id,
                            'filename': tool.filename,
                            'product_id': tool.product_id.id,
                            'location_id': master_tools_obj.location_id.id,
                        }))
                    detail_lines_data.append((0, 0, {
                        'week': str(weeks),
                        'periode_bulan': month_now,
                        'tahun': year_now,
                        'checklist_detail_ids': weekly_lines
                    }))
                    weeks += 1

            checklist.write({'line_ids': detail_lines_data})
            if checklist.state == 'draft':
                checklist.write({
                    'state': 'open',
                    'confirm_uid': self._uid,
                    'confirm_date': datetime.now()
                })

        return True

        # 14: private methods
    def _is_previous_transaction_done(self, company_id, pic_id, category_master_tool_id):
        previous_checklists = self.env['tw.checklist.tools'].search([
            ('company_id', '=', company_id),
            ('pic_id', '=', pic_id),
            ('category_master_tool_id', '=', category_master_tool_id),
            ('state', '!=', 'done')
        ])
        if previous_checklists:
            return True