from xml.dom import ValidationErr
from odoo import models, fields, api

class StockOpnameLocation(models.Model):
    _name = "tw.stock.opname.location"
    _description = "Stock Opname Location"

    filename_upload_foto_selfie = fields.Char( string="Filename Upload Foto Selfie", help="")
    filename_upload_foto_all_stock = fields.Char( string="Filename Upload Foto All Stock", help="")

    file_foto_selfie = fields.Binary( string="File Foto Selfie", help="")
    file_foto_selfie_show = fields.Binary( string="File Foto Selfie show", compute='_compute_file_foto_opname' ,help="")
    file_foto_all_stock = fields.Binary( string="File Foto All Stock", help="")
    file_foto_all_stock_show = fields.Binary( string="File Foto All Stock show", compute='_compute_file_foto_opname' ,help="")

    jumlah_unit = fields.Integer(string='Jumlah Unit')

    opname_id = fields.Many2one('tw.stock.opname', ondelete="cascade")
    location_id = fields.Many2one('stock.location', string="Location")
    condition_opname_ids = fields.One2many('tw.stock.opname.condition','location_id')
    
    @api.depends('filename_upload_foto_selfie','filename_upload_foto_all_stock')
    def _compute_file_foto_opname(self):
        for record in self:
            record.file_foto_selfie_show = False
            record.file_foto_all_stock_show = False

            if record.filename_upload_foto_selfie :
                foto = self.env['tw.config.files'].suspend_security().get_file(record.filename_upload_foto_selfie)
                record.file_foto_selfie_show = foto

            if record.filename_upload_foto_all_stock :
                foto = self.env['tw.config.files'].suspend_security().get_file(record.filename_upload_foto_all_stock)
                record.file_foto_all_stock_show = foto
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            foto_selfie = False
            foto_all_stock = False

            if vals.get('file_foto_selfie'):
                foto_selfie = vals['file_foto_selfie']
                vals['file_foto_selfie'] = False
            if vals.get('file_foto_all_stock'):
                foto_all_stock = vals['file_foto_all_stock']
                vals['file_foto_all_stock'] = False
            if vals.get('file_foto_selfie'):
                foto_selfie = vals['file_foto_selfie']
                vals['file_foto_selfie'] = False
            if vals.get('file_foto_all_stock'):
                foto_all_stock = vals['file_foto_all_stock']
                vals['file_foto_all_stock'] = False

            stock_opname = super().create(vals)
            if not stock_opname or not stock_opname.opname_id:
                raise ValidationErr("Data opname_id tidak valid atau tidak memiliki relasi opname_id.")
                
            file_name = stock_opname.opname_id.name.replace("/","-")

            if foto_selfie:
                tmp_file = str(vals['filename_upload_foto_selfie']).split('.')
                filename_up = str('foto_selfie')+'-'+str(file_name)+'-'+str(stock_opname.id)+'.'+tmp_file[len(tmp_file) - 1]
                self.env['tw.config.files'].suspend_security().upload_file(filename_up, foto_selfie)
                stock_opname.filename_upload_foto_selfie = filename_up
            if foto_all_stock:
                tmp_file = str(vals['filename_upload_foto_all_stock']).split('.')
                filename_up = str('foto_all_stock')+'-'+str(file_name)+'-'+str(stock_opname.id)+'.'+tmp_file[len(tmp_file) - 1]
                self.env['tw.config.files'].suspend_security().upload_file(filename_up, foto_all_stock)
                stock_opname.filename_upload_foto_all_stock = filename_up
        return stock_opname
    
    def write(self,vals):
        file_name = self.opname_id.name.replace("/","-")
        if vals.get('file_foto_selfie'):
            foto_selfie = vals['file_foto_selfie']
            vals['file_foto_selfie'] = False
            tmp_file = str(vals['filename_upload_foto_selfie']).split('.')
            filename_up = str('foto_selfie')+'-'+str(file_name)+'-'+str(self.id)+'.'+tmp_file[len(tmp_file) - 1]
            self.env['tw.config.files'].suspend_security().upload_file(filename_up, foto_selfie)
            vals['filename_upload_foto_selfie'] = filename_up
        if vals.get('file_foto_all_stock'):
            foto_all_stock = vals['file_foto_all_stock']
            vals['file_foto_all_stock'] = False
            tmp_file = str(vals['filename_upload_foto_all_stock']).split('.')
            filename_up = str('foto_all_stock')+'-'+str(file_name)+'-'+str(self.id)+'.'+tmp_file[len(tmp_file) - 1]
            self.env['tw.config.files'].suspend_security().upload_file(filename_up, foto_all_stock)
            vals['filename_upload_foto_all_stock'] = filename_up

        return super(StockOpnameLocation,self).write(vals) 
    
    def create_lokasi(self,opname_id):
        query = f"""
            SELECT 
                detail.location_id as location_id
            FROM tw_stock_opname_detail detail
            WHERE detail.opname_id = {opname_id}
            GROUP BY location_id
        """
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        
        condition_obj = self.env['tw.selection'].sudo().search([
            ('active','=',True),
            ('type','=','SoCondition'),
        ])
        condition_vals = [[0, 0, { 'condition_id': condition.id }] for condition in condition_obj]
        
        lokasi_records = []
        for lokasi in data:
            lokasi_record = self.env['tw.stock.opname.location'].create({
                'opname_id': opname_id,
                'location_id': lokasi.get('location_id'),
                'condition_opname_ids': condition_vals
            })
            lokasi_records.append(lokasi_record)
        return self.env['tw.stock.opname.location'].browse([loc.id for loc in lokasi_records])
    
    def action_view_file_foto_selfie(self):
        form_id = self.env.ref('tw_stock_opname.view_tw_stock_opname_foto_selfie_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'File Foto Selfie',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.stock.opname.location',
            'views': [(form_id, 'form')],
            'res_id':self.id,
            'target':'new'
        }
        
    def action_view_file_foto_all_stock(self):
        form_id = self.env.ref('tw_stock_opname.view_tw_stock_opname_foto_all_stock_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'File Foto All Stock',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.stock.opname.location',
            'views': [(form_id, 'form')],
            'res_id':self.id,
            'target':'new'
        }