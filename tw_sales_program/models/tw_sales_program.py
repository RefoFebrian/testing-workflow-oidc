# 1: imports of python lib
from datetime import datetime, timedelta
import base64
import xlrd

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwSalesProgram(models.Model):
    _name = "tw.sales.program"
    _description = "Master Sales Program"

    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False

    # 8: fields
    name = fields.Char('Name')
    partner_ref = fields.Char('Kode Program MD', size=50)
    note = fields.Text('Keterangan')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    active = fields.Boolean('Active', default=True)
    file = fields.Binary('File')
    filename = fields.Char('Filename')
    promo_value = fields.Float('Nilai Promo', compute='_compute_get_max', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('editable', 'Editable'),
        ('on_revision', 'On Revision')
    ], string='State', default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    # 9: relation fields
    sales_program_type_id = fields.Many2one('tw.selection', string='Tipe Sales Program', domain=[('type','=','MasterSalesProgram')])
    company_id = fields.Many2one('res.company', string='Branch', default=_get_default_branch)
    area_id = fields.Many2one('res.area', string='Area')
    sales_program_type_name = fields.Char('Sales Program', related='sales_program_type_id.value')
    line_ids = fields.One2many('tw.sales.program.line', 'sales_program_id', string='Sales Program Lines')

    # 10: constraints & sql constraints
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for data in self:
            if data.start_date and data.end_date:
                if data.start_date > data.end_date:
                    raise ValidationError(_('Periode Start Date tidak boleh lebih besar dari End Date.'))

    # 11: compute/depends & on change methods
    @api.depends('line_ids')
    def _compute_get_max(self):
        """
        This method is used to compute get the max of total discount on sales program discount line.
        """
        for data in self:
            discount_total = [line.discount_total for line in data.line_ids]
            data.promo_value = max(discount_total) if discount_total else 0

    @api.onchange('sales_program_type_id')
    def _onchange_sales_program_type_id(self):
        for data in self:
            if data.sales_program_type_name == 'Program Subsidi':
                data.division = 'Unit'

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        program_subsidi_id = self.env.ref(
            'tw_sales_program.tw_selection_type_master_sales_program_program_subsidi',
            raise_if_not_found=False
        )
        for vals in vals_list:
            if not vals.get('division') and program_subsidi_id and vals.get('sales_program_type_id') == program_subsidi_id.id:
                vals['division'] = 'Unit'

        return super().create(vals_list)

    def unlink(self):
        for data in self:
            if data.state != 'draft':
                raise Warning(f'Sales Program {data.sales_program_type_id.name.title()} tidak bisa didelete !')
        return super(TwSalesProgram, self).unlink()
    
    def copy(self, default=None, context=None):
        sales_program_lines = []
        if default is None:
            default = {}
        for data in self:
            start_date = data.start_date + timedelta(days=1)
            end_date = data.start_date + timedelta(days=2)
            default.update({
                'sales_program_type_id': data.sales_program_type_id.id if data.sales_program_type_id else False,
                'company_id': data.company_id.id,
                'division': data.division if data.division else False,
                'area_id': data.area_id.id if data.area_id else False,
                'name': data.name + ' (Copy)',
                'start_date': start_date,
                'end_date': end_date,
                'note': data.note,
                'product_id': data.product_id.id if data.product_id else False,
                'finco_id': [(6, 0, data.finco_id.ids)] if data.finco_id else False,
                'subsidy_type': data.subsidy_type,
                'state': 'draft',
                'partner_ref': data.partner_ref,
                'active': True,
            })
            for line in data.line_ids:
                sales_program_lines.append([0, False, {
                    'sales_program_type_id': line.sales_program_type_id.id if line.sales_program_type_id else False,
                    'product_tmpl_id': line.product_tmpl_id.id,
                    'qty': line.qty,
                    'dp_type': line.dp_type,
                    'amount_dp': line.amount_dp,
                    'discount_ahm': line.discount_ahm,
                    'discount_md': line.discount_md,
                    'discount_dealer': line.discount_dealer,
                    'discount_finco': line.discount_finco,
                    'discount_others': line.discount_others
                }])
            default.update({'line_ids': sales_program_lines})
        return super().copy(default=default)

    # 13: action methods
    def action_sales_program_tree(self, category='program_subsidi_barang'):
        domain = []
        name = 'Program Subsidi Barang'
        sales_program_type_id = self.env.ref('tw_sales_program.tw_selection_type_master_sales_program_subsidi_barang').id
        if category == 'program_subsidi':
            name = 'Program Subsidi'
            sales_program_type_id = self.env.ref('tw_sales_program.tw_selection_type_master_sales_program_program_subsidi').id
        elif category == 'program_voucher':
            name = 'Program Voucher'
            sales_program_type_id = self.env.ref('tw_sales_program.tw_selection_type_master_sales_program_program_voucher').id
        domain += [('sales_program_type_id','=',sales_program_type_id)]
        list_view_id = self.env.ref('tw_sales_program.tw_sales_program_list_view').id
        form_view_id = self.env.ref('tw_sales_program.tw_sales_program_form_view').id
        search_view_id = self.env.ref('tw_sales_program.tw_sales_program_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.sales.program',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1,
                'default_sales_program_type_id': sales_program_type_id,
                'default_division': 'Unit' if category == 'program_subsidi' else False
            },
        }
    
    def button_dummy(self):
        return True
    
    def action_download_format_file(self):
        format_upload_obj = self.env['tw.format.upload'].suspend_security().search([
            ('name','=','upload master sales program'),
            ('active','=',True)
        ], limit=1)
        if format_upload_obj:
            return {
                'type': 'ir.actions.act_url',
                'name': 'contract',
                'url': f'/web/content/tw.format.upload/{format_upload_obj.id}/file_format_show/{format_upload_obj.filename_upload_format}?download=true'
            }
        else:
            raise Warning('Maaf, format template file belum tersedia.')
    
    def action_import(self):
        if not self.file:
            raise Warning('File belum diupload, mohon upload file terlebih dahulu !')
        data = base64.decodebytes(self.file)
        excel = xlrd.open_workbook(file_contents = data)
        sheet = excel.sheet_by_index(0)
        lines = []
        error = ''
        ncols = 9
        if sheet.ncols != ncols:
            raise Warning(f'Jumlah Kolom pada Format Upload tidak sama dengan {str(ncols)}.\n\nDetail dan Urutan Kolom:\nProduct Code, Qty, Tipe DP, DP Minimal, Diskon AHM, Diskon MD, Diskon Dealer, Diskon Finco dan Diskon Voucher')
        for rx in range(1, sheet.nrows):
            product_code = str(sheet.cell(rx, 0).value)
            product_tmpl_obj = self.env['product.template'].search([('default_code','=',product_code)], limit=1)
            if not product_tmpl_obj:
                error += "\nProduct Code '%s' tidak ditemukan" % (product_code)
                continue
            qty = sheet.cell(rx, 1).value or 0
            dp_type = sheet.cell(rx, 2).value or False
            amount_dp = sheet.cell(rx, 3).value or False
            diskon_ahm = sheet.cell(rx, 4).value or 0
            diskon_md = sheet.cell(rx, 5).value or 0
            diskon_dealer = sheet.cell(rx, 6).value or 0
            diskon_finco = sheet.cell(rx, 7).value or 0
            discount_others = sheet.cell(rx, 8).value or 0
            vals = {'product_tmpl_id': product_tmpl_obj.id}
            if self.sales_program_type_name in ('Program Subsidi Barang', 'Program Subsidi'):
                vals.update({
                    'discount_ahm': diskon_ahm,
                    'discount_md': diskon_md,
                    'discount_dealer': diskon_dealer,
                    'discount_finco': diskon_finco
                })
                if self.sales_program_type_name == 'Program Subsidi Barang':
                    vals.update({'qty': qty})
                else:
                    vals.update({'amount_dp': amount_dp})
                    if dp_type:
                        vals.update({'dp_type': dp_type.lower()})
            else:
                vals = {'discount_others': discount_others}
            lines.append((0, 0, vals))

        if error:
            raise Warning(str(error))
        self.line_ids = lines
        form_view_id = self.env.ref('tw_sales_program.tw_sales_program_form_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import Sales Program',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.sales.program',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_view_id, 'form')],
            'target': 'current'
        }

    # 14: private methods