# -*- coding: utf-8 -*-

# 1: imports of python lib
import qrcode
import base64
import io
from datetime import date, datetime, timedelta,time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWPrintGenerateQRCode(models.Model):
    _name = "tw.print.generate.qr.code"
    _description = "Print Generate QR Code"
    _order = "create_date desc"
    
    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now()

    # 8: fields
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    description = fields.Text(string='Keterangan')
    date = fields.Date(string='Date', default=_get_default_date)
    print_count = fields.Integer(string='Jumlah Print')
    print_to = fields.Integer(string='Cetakan ke', default=0)
    is_generate = fields.Boolean(string='Generate', default=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='Status', default='draft')
    
    # 9: relation fields
    company_id = fields.Many2one('res.company', string='Branch', default=lambda self: self.env.company)
    qr_code_ids = fields.One2many('tw.print.generate.qr.code.line', 'print_qr_code_id', string='List QR Code')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            seq_name = self.env['ir.sequence'].with_company(record.company_id).get_sequence_code('PRINT/QR', record.company_id.code)
            record.name = seq_name

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        return super(TWPrintGenerateQRCode, self).create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning("Tidak bisa menghapus data yang berstatus selain draft.")
            if rec.is_generate:
                raise Warning("Tidak bisa menghapus data yang sudah di generate.")
        return super(TWPrintGenerateQRCode, self).unlink()

    # 13: action methods
    def action_listing_qr_code(self):
        if not self.qr_code_ids:
            if self.print_count < 10:
                raise Warning("Jumlah Print tidak boleh kurang dari 10")
            
            qr_code_obj = self.env['tw.qr.code.unit'].suspend_security().search([
                ('state', '=', 'New'),
                ('company_id', '=', self.company_id.id)
            ], limit=self.print_count)
            if qr_code_obj:
                if len(qr_code_obj) < self.print_count:
                    raise Warning(f"Jumlah QR Code yang tersedia sebanyak {len(qr_code_obj)} tidak mencukupi jumlah yang diminta sebanyak {self.print_count}\nSilahkan generate kode unik terlebih dahulu!")

                self.qr_code_ids = [[0, 0, {
                    'print_qr_code_id': self.id,
                    'name': qr.name,
                    'qr_code_id': qr.id,
                }] for qr in qr_code_obj]
                
                self.is_generate = True
            else:
                raise Warning("Kode Unik tidak tersedia, silahkan generate kode unik terlebih dahulu!")
        else:
            raise Warning("Kode Unik sudah tergenerate!")
            
    def action_print_barcode_label(self):
        self.ensure_one()
        if not self.qr_code_ids:
            raise Warning("Tidak ada kode unik yang masuk listing, Harap klik tombol Listing QR Code terlebih dahulu!")
        
        self.print_to += 1
        if self.state == 'draft':
            self.state = 'done'
            
        datas = {
            'id': self.id,
            'model': 'tw.print.generate.qr.code',
            'user': self._uid
        }
        return self.env.ref('tw_qr_code_unit.qr_code_unit_report').report_action(self, data=datas)
    
    def action_reprint_barcode_label(self):
        form_id = self.env.ref('tw_qr_code_unit.tw_reprint_generate_qr_code_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reprint QR Code',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.print.generate.qr.code',
            'views': [(form_id, 'form')],
            'res_id': self.id,
            'target':'new'
        }

    # 14: private methods
    
