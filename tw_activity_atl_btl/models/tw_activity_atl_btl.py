# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWActivityPlan(models.Model):
    _name = "tw.activity.atl.btl"
    _description = "Activity Plan ATL & BTL"
    _order = "id desc"
    
    # 7: defaults methods
    def _get_year_default(self):
        return date.today().year
    
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False  

    # 8: fields
    name = fields.Char('Name')
    month = fields.Selection([
        ('1', 'Januari'), ('2', 'Februari'), ('3', 'Maret'),
        ('4', 'April'), ('5', 'Mei'), ('6', 'Juni'),
        ('7', 'Juli'), ('8', 'Agustus'), ('9', 'September'),
        ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember'),
    ], string='Month')
    year = fields.Selection(
        [(str(num), str(num)) for num in range(2010, (datetime.now().year) + 3)],
        string='Year',
        default=str(datetime.now().year)
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('open', 'Open'),
        ('done', 'Done')], default='draft')
    total_cost_btl = fields.Float('Total BTL Cost', compute="compute_total_biaya_btl", store=True)
    sum_data_confirm = fields.Float('Jml Data', compute='compute_jml_data')
    
    # 8.1 Audit Trail fields
    open_uid = fields.Many2one('res.users', 'Open by')
    open_date = fields.Datetime('Open on')
    done_uid = fields.Many2one('res.users', 'Done by')
    done_date = fields.Datetime('Done on')

    # 9: relation fields
    company_id = fields.Many2one('res.company', 'Branch', default=_get_default_branch)
    activity_line_ids = fields.One2many('tw.activity.atl.btl.line', 'activity_id', 'Detail')
    activity_line_confirm_ids = fields.One2many('tw.activity.atl.btl.line', 'activity_id', domain=[('state', '=', 'confirmed')], string="Status")

    # 10: constraints & sql constraints
    @api.constrains('company_id', 'month', 'year')
    def duplicate_activity_btl(self):
        for record in self:
            if self.search_count([('company_id', '=', record.company_id.id),
                                  ('month', '=', record.month),
                                  ('year', '=', record.year)]) > 1:
                raise Warning('Activity Plan tidak boleh sama !\n Coba gunakan bulan atau tahun atau dealer yang berbeda !')
                
    # TODO: Bisa di uncomment kalo perlu fitur ini.
    # di commend karena ketika migrasi kena jegatan ini
    # @api.constrains('year')
    # def check_year(self):
    #     for record in self:
    #         year_now = datetime.now().year
    #         if int(record.year) < int(year_now):
    #             raise Warning('Tidak bisa memilih tahun yang kurang dari tahun saat ini!')

    @api.constrains('activity_line_ids')
    def _check_activity_lines(self):
        for record in self:
            if not record.activity_line_ids:
                raise Warning(_("Activity Detail tidak boleh kosong!"))

    @api.constrains('month', 'year')
    def _check_month_year(self):
        for record in self:
            if record.month and record.year:
                if int(record.month) < int(date.today().month) and int(record.year) <= int(date.today().year):
                    raise Warning(_("Tidak bisa memilih bulan yang kurang dari bulan saat ini!"))
    
    # 11: compute/depends & on change methods
    @api.depends('activity_line_ids.total_cost')
    def compute_total_biaya_btl(self):
        total = 0
        for activity_line in self.activity_line_ids:
            if activity_line.state != 'reject':
                total += activity_line.total_cost
        self.total_cost_btl = total
    
    @api.depends('activity_line_confirm_ids')
    def compute_jml_data(self):
        total = 0
        if self.activity_line_confirm_ids:
            total = len(self.activity_line_confirm_ids)
        self.sum_data_confirm = total

    @api.onchange('month', 'year')
    def _onchange_month_year(self):
        self._check_month_year()

    # @api.onchange('year')
    # def onchange_year(self):
    #     year_now = datetime.now().year
    #     if int(self.year) < int(year_now):
    #         raise Warning('Tidak bisa memilih tahun yang kurang dari tahun saat ini!')

    # 12: override methods
    def get_sequence(self, branch_code):
        seq = self.env['ir.sequence']
        seq_name = '{0}/{1}'.format('BTL', branch_code)
        ids = seq.search([('name', '=', seq_name)])
        if not ids:
            prefix = '/%(y)s/%(month)s/'
            prefix = seq_name + prefix
            ids = seq.create(
                {
                    'name': seq_name,
                    'implementation': 'standard', 
                    'prefix': prefix,
                    'padding': 5,
                }
            )
        return ids.next_by_id()
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            branch_src = self.env['res.company'].sudo().search([('id', '=', vals.get('company_id'))], limit=1)
            if not branch_src:
                raise Warning('Company/Dealer tidak ditemukan untuk nilai yang diberikan!')
            
            doc_code = branch_src.code
            vals['name'] = self.get_sequence(doc_code)
        
        return super(TWActivityPlan, self).create(vals_list)

    def write(self, vals):
        res = super(TWActivityPlan, self).write(vals)
        return res 

    # 13: action methods
    def action_done_activity_atl_btl(self):
        activity_atl_btl_objs = self.search([
            ('month', '<', str(date.today().month)),
            ('year', '<=', str(date.today().year))
        ])
        if activity_atl_btl_objs:
            activity_atl_btl_objs.write({'state': 'done', 'done_uid': self._uid, 'done_date': datetime.now()})

            # Set 'foto' field to None for activity lines meeting the criteria
            activity_atl_btl_line_objs = self.env['tw.activity.atl.btl.line'].search([
                ('activity_id', 'in', activity_atl_btl_objs.ids),
                ('loc_photo', '!=', False)
            ])
            activity_atl_btl_line_objs.write({'loc_photo': None})
        else:
            raise Warning("Activity BTL tidak bisa dilakukan penyelesaian pada bulan berjalan (bulan saat ini)")
    
    def action_result_activity_btl(self):
        list_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_list_view').id
        form_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_form_view').id
        search_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_result_filter').id
        tgl = str(date.today())
        domain = [('state', 'in', ['open', 'done'])]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Activity Results',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.activity.atl.btl',
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
            'search_view_id': search_id,
            'context': {
                'result_btl': True,
                'search_default_state_open':1,
                'create': False,
                'edit': False,
                'delete': False,
            },
        }
    
    def action_add_activity(self):
        date_now = date.today()
        year = date_now.year
        month = date_now.month
        if int(month) == 12 and int(self.month) == 1:
            year += 1
            month = 1

        if (int(month) > int(self.month)) or (int(year) != int(self.year)):
            raise Warning('Periode dan Tahun sudah lewat, Sudah tidak bisa melakukan add activity!')
    
        form_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_line_all_form_view').id
        context = {
            'default_activity_id': self.id,
            'add_activity': True,
            'readonly_by_pass': 1,
        }
        if self.state in ('approved', 'open'):
            context.update({
                'default_state': 'draft',
            })

        return {
            'name': ('Add Activity'),
            'res_model': 'tw.activity.atl.btl.line',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form',
            'context': context,
        }

    def action_print_btl(self):
        active_ids = self.env.context.get('active_ids')
        user = self.env['res.users'].browse(self._uid).name
        detail_ids = []
        total_biaya_tdm = 0
        # TODO: need confirmation if leasing is need it
        # total_biaya_leasing = 0
        total_biaya_tdm_ppn = 0
        # total_biaya_leasing_ppn = 0

        for line in self.activity_line_ids:
            if line.state == 'done':
                biaya_ids = []
                history_ids = [] 
                detail_unit_ids = False
                activity_point_obj = line.mapping_activity_id.activity_point_id

                if len(line.detail_cost_ids) > 0:
                    for biaya in line.detail_cost_ids:
                        total_biaya_tdm += biaya.amount
                        total_biaya_tdm_ppn += biaya.subtotal
                        biaya_ids.append({
                            'partner_id': biaya.partner_id.name if biaya.partner_id != None else '',
                            'submission_type': biaya.submission_type_id.value,
                            'tax_id': biaya.tax_id.id,
                            'tax_name': biaya.tax_id.name,
                            'amount': biaya.amount,
                            'subtotal': biaya.subtotal,
                            'note': biaya.note,
                        })
                tot_history = len(line.history_location_ids)
                start = 0
                if tot_history > 0:
                    categ_list = {}
                    for history in line.history_location_ids:
                        start += 1
                        history_ids.append({
                            'month': history.month,
                            'qty': history.qty,
                        })

                        if start == tot_history:
                            for unit in history.detail_ids:
                                if not categ_list.get(unit.categ_id.name):
                                    categ_list[unit.categ_id.name] = {'categ_id': unit.categ_id.name, 'qty': 1}
                                else:
                                    categ_list[unit.categ_id.name]['qty'] += 1

                            detail_unit_ids = categ_list.values()
                
                detail_ids.append({
                    'name': line.name,
                    'alamat': line.street,
                    'rt': line.rt,
                    'rw': line.rw,
                    'kelurahan': line.sub_district_id.name,
                    'kecamatan': line.district_id.name,
                    'city': line.city_id.name,
                    'start_date': line.start_date,
                    'end_date': line.end_date,
                    'pic': line.pic_id.name,
                    'nik': line.registry_number,
                    'jabatan': line.job,
                    'no_telp': line.phone_number,
                    'display_unit': line.display_unit,
                    'target_unit': line.target_unit,
                    'pencapaian_unit': sum([h.qty for h in line.history_location_ids]),
                    'biaya_ids': biaya_ids,
                    'history_ids': history_ids,
                    'detail_unit_ids': detail_unit_ids,
                    'jarak': line.mapping_activity_id.distance if line.mapping_activity_id.distance else '0',
                    'waktu': line.mapping_activity_id.estimated_travel_time if line.mapping_activity_id.estimated_travel_time else '0',
                    'foto': line.loc_photo_show,
                })

        if len(detail_ids) < 1:
            raise Warning('Detail Activity Plan tidak ada yang berstatus Done, Minimal ada 1 data yang sudah bersatus Done untuk dapat diprint BTL !')
        
        # TODO: butuh di confirm apakah di perlukan untuk leasing
        datas = {
            'ids': active_ids,
            'user': user,
            'company_id': str(self.company_id.name),
            'periode': str(self.name_get().pop()[1]),
            'total_biaya_tdm': total_biaya_tdm,
            # 'total_biaya_leasing':total_biaya_leasing,
            'total_biaya_tdm_ppn': total_biaya_tdm_ppn,
            # 'total_biaya_leasing_ppn':total_biaya_leasing_ppn,
            'detail_ids': detail_ids,
            'create_uid': self.create_uid.name,
            'create_date': self.create_date,
            'approved_uid': self.approved_uid.name,
            'approved_date': (self.approved_date + relativedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'open_uid': self.open_uid.name if self.open_uid else self.approved_uid.name,
            'open_date': (self.open_date + relativedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') if self.open_date else (self.approved_date + relativedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
        }
        return self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_report').report_action(self.id, data=datas)
    
    # 14: private methods
    def name_get(self):
        if self._context is None:
            self._context = {}
        res = []
        for record in self:
            a = (calendar.month_name[int(record.month)])
            tit = "[%s - %s] %s" % (a, record.year, record.name)
            res.append((record.id, tit))
        return res
