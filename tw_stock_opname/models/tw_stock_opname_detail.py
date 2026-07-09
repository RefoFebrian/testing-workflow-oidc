from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import datetime

class StockOpnameDetail(models.Model):
    _name = "tw.stock.opname.detail"
    _description = "Stock Opname Detail"
    _order = 'perhitungan_ke DESC'

    def _get_default_datetime(self):
        return datetime.now()

    product_code = fields.Char('Product Code', related='product_id.default_code', store=True)
    qty_system = fields.Integer(string='Qty System')
    perhitungan_ke = fields.Integer(string='Perhitungan Ke', default=0)
    qty_count = fields.Integer(string='Qty Stock Opname')
    selisih = fields.Integer(string='Selisih')
    is_recount = fields.Boolean(string='Is Recount')
    count_date = fields.Datetime(string='Datetime Submit')
    has_accessories = fields.Boolean(string='Has Accessories')
    is_showroom = fields.Boolean(string='Is Showroom')
    rfs = fields.Boolean(string='RFS')
    latitude = fields.Float('Latitude', digits=(3, 6))
    longtitude = fields.Float('Longtitude', digits=(3,6))
    price = fields.Float(string='Harga (Rp)', digits='Product Price')
    penjelasan_nrfs = fields.Char('Penjelasan NRFS')
    maps = fields.Char(string='Maps')
    alasan_reject = fields.Text(string='Alasan Reject')
    chassis_no = fields.Char(string='Nomor Rangka')
    maps_embed = fields.Html(string="Map", compute="_compute_maps_embed", sanitize=False)
    reason = fields.Char('Reason')

    file_foto = fields.Binary( string="File Foto", help="")
    filename_foto = fields.Char( string="Filename Foto", help="")
    filename_upload = fields.Char( string="Filename Upload", help="")
    file_foto_show = fields.Binary( string="File Foto show", compute='_compute_file_foto' ,help="")

    reject_uid = fields.Many2one('res.users', string='Reject by')
    reject_date = fields.Datetime('Reject on')

    # Selection Fields 
    state = fields.Selection([
        ('open', 'Open'),
        ('selisih', 'Selisih'),
        ('anomali', 'Anomali'),
        ('done', 'Done'),   
    ], string='Status', readonly=True, default='open')
    # state = fields.Selection(related="opname_id.state", string='Status SO')

    employee_id = fields.Many2one('hr.employee', string='Penanggung Jawab',domain="[('company_id','=',parent.company_id)]")
    opname_id = fields.Many2one('tw.stock.opname', ondelete="cascade") 
    product_id = fields.Many2one('product.product', string="Product")
    location_id = fields.Many2one('stock.location', string="Lokasi")
    lot_id = fields.Many2one('stock.lot',string="No Mesin")
    history_opname_ids = fields.One2many('tw.stock.opname.history','opname_detail_id')

    @api.depends('filename_upload')
    def _compute_file_foto(self):
        for detail in self:
            if detail.filename_upload:
                foto = self.env['tw.config.files'].suspend_security().get_file(detail.filename_upload)
                self.file_foto_show = foto
            else : 
                self.file_foto_show = False
    
    @api.model_create_multi
    def create(self,vals_list):
        file = []
        for vals in vals_list:
            if vals.get('file_foto'):
                file.append(vals['file_foto'])
                vals['file_foto'] = False
        
        create_list = super(StockOpnameDetail,self).create(vals_list)
        for n,create in enumerate(create_list):
            if file and file[n]:
                tmp_file = vals['filename'].split('.')
                if tmp_file[len(tmp_file) - 1] not in ('pdf', 'PDF'):
                    raise Warning('Perhatian!\nFile Pendukung "%s" Harus PDF' % str(create.type))
                
                filename_up = str('foto_no_rangka')+'-'+str(create.lot_id.chassis_no)+'-'+str(create.id)+'.'+tmp_file[len(tmp_file) - 1]
                self.env['tw.config.files'].suspend_security().upload_file(filename_up, file[n])

                check_size = self.env['tw.config.files'].suspend_security().cek_size(filename_up)
                if check_size > 5000000:
                    raise Warning('Perhatian!\nUkuran File "%s" Melebihi Maksimal, File Pendukung Maks Size 5MB' % str(create.opname_id.code))
                
                create.filename_upload = filename_up
                if create:
                    create.filename_download = filename_up

                if create.lot_id:
                    create.chassis_no = create.lot_id.chassis_no 
        return create_list
    
    def write(self,vals):
        if vals.get('file_foto'):
            file = vals['file_foto']
            vals['file_foto'] = False
            tmp_file = vals['filename_foto'].split('.')
            filename_up = str('foto_no_rangka')+'-'+str(self.lot_id.name)+'-'+str(self.id)+'.'+tmp_file[len(tmp_file) - 1]
            self.env['tw.config.files'].suspend_security().upload_file(filename_up, file)
            vals['filename_upload']=filename_up
        return super(StockOpnameDetail,self).write(vals)

    def action_reject(self):
        form_id = self.env.ref('tw_stock_opname.view_tw_stock_opname_reject_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': ('Alasan Reject'),
            'res_model': 'tw.stock.opname.detail',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(form_id, 'form')],
            'target':'new',
            'res_id': self.id,
        }
    
    def reject(self):
        self.write({ 
            'reject_uid':self._uid,
            'reject_date':self._get_default_datetime(),
            'state': 'open',
            'alasan_reject': self.alasan_reject,
            'count_date':False,
            'qty_count': False,
            'selisih': False,
            'is_recount': True, 
            'latitude' : False,
            'longtitude' : False,
            'maps' : False,
            'rfs' : False,
            'penjelasan_nrfs' : False,
            'file_foto' : False,
            'filename_foto' : False
        }) 
        
    def action_view_file_foto_unit(self):
        form_id = self.env.ref('tw_stock_opname.view_tw_stock_opname_foto_unit_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'File Foto Unit',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.stock.opname.detail',
            'views': [(form_id, 'form')],
            'res_id':self.id,
            'target':'new'
        }
        
    def action_view_file_maps(self):
        form_id = self.env.ref('tw_stock_opname.view_tw_stock_opname_maps_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maps',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.stock.opname.detail',
            'views': [(form_id, 'form')],
            'res_id':self.id,
            'target':'new'
        }
    
    def _compute_maps_embed(self):
        for rec in self:
            if rec.latitude and rec.longtitude:
                rec.maps_embed = f"""
                    <iframe width="100%" height="300" style="border:0"
                        loading="lazy"
                        allowfullscreen
                        referrerpolicy="no-referrer-when-downgrade"
                        src="{rec.maps}&output=embed">
                    </iframe>
                """
            else:
                rec.maps_embed = "<p>No location provided</p>"

    