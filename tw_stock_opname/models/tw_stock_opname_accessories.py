from odoo import models, fields, api

class StockOpnameAccessories(models.Model):
    _name = "tw.stock.opname.accessories"
    _description = "Stock Opname Accessories"

    is_count = fields.Boolean(string='Is Count')
    qty_system = fields.Integer(string='Qty System') 
    qty_good = fields.Integer(string='Qty Good') 
    qty_not_good = fields.Integer(string='Qty Not Good') 
    alasan_notgood = fields.Char(string='Alasan Not Good') 
    segment_name = fields.Char('Segment', related='product_id.product_tmpl_id.categ_id.name', store=True)
    reason = fields.Char('Reason')

    file_foto = fields.Binary( string="File Foto", help="")
    filename_upload = fields.Char( string="Filename Upload", help="")
    file_foto_show = fields.Binary( string="File Foto show", compute='_compute_file_foto' ,help="")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('selisih', 'Selisih'),
        ('anomali', 'Anomali'),
        ('done', 'Done'),
    ], string='Status', default='draft')

    location_id = fields.Many2one('stock.location', string="Lokasi")
    product_id = fields.Many2one('product.product', string="Product")
    opname_id = fields.Many2one('tw.stock.opname', string="Stock Opname")
    employee_id = fields.Many2one('hr.employee', string='Penanggung Jawab', domain="[('company_id','=',parent.company_id)]")

    @api.depends('filename_upload')
    def _compute_file_foto(self):
        for detail in self:
            if detail.filename_upload:
                foto = self.env['tw.config.files'].suspend_security().get_file(detail.filename_upload)
                detail.file_foto_show = foto
            else : 
                detail.file_foto_show = False

    def action_view_file_foto_accessories(self):
        form_id = self.env.ref('tw_stock_opname.view_tw_stock_opname_foto_accessories_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'File Foto Accessories',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.stock.opname.accessories',
            'views': [(form_id, 'form')],
            'res_id':self.id,
            'target':'new'
        }

    @api.model_create_multi
    def create(self,vals_list):
        create_list = super(StockOpnameAccessories,self).create(vals_list)
        for n,create in enumerate(create_list):
            vals = vals_list[n]
            if vals.get('file_foto') and vals.get('filename_upload'):
                file = vals['file_foto']
                tmp_file = vals['filename_upload'].split('.')
                
                filename_up = str('foto_accessories')+'-'+str(create.product_id.id)+'-'+str(create.id)+'.'+tmp_file[len(tmp_file) - 1]
                self.env['tw.config.files'].suspend_security().upload_file(filename_up, file)

                check_size = self.env['tw.config.files'].suspend_security().cek_size(filename_up)
                if check_size > 5000000:
                    raise Warning('Perhatian!\nUkuran File "%s" Melebihi Maksimal, File Pendukung Maks Size 5MB' % str(create.opname_id.code))
                
                create.filename_upload = filename_up
        return create_list
    
    def write(self,vals):
        if vals.get('file_foto') and vals.get('filename_upload'):
            file = vals['file_foto']
            vals['file_foto'] = False
            tmp_file = vals['filename_upload'].split('.')
            filename_up = str('foto_accessories')+'-'+str(self.product_id.id)+'-'+str(self.id)+'.'+tmp_file[len(tmp_file) - 1]
            self.env['tw.config.files'].suspend_security().upload_file(filename_up, file)
            vals['filename_upload']=filename_up
        return super(StockOpnameAccessories,self).write(vals)