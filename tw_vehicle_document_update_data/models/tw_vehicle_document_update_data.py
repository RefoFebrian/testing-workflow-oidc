# 1: import of python lib

# 2: import of known third party lib
# 3: import of odoo
from odoo import models, fields, api
# 4: import from odoo module
from odoo.exceptions import UserError as Warning
# 5: local imports
import string
# 6: import of unknown third party lib
from markupsafe import Markup
from datetime import datetime

STATE_SELECTION = [
        ("draft", "Draft"),
        ("confirm", "Confirmed"),
        ("cancel", "Cancelled")
    ]


class TwVehicleDocumentUpdateData(models.Model):
    _name = "tw.vehicle.document.update.data"
    _description = "Permohonan Perubahan Data"
    _order = "id desc"
    _rec_name = "lot_id"
    _inherit = ["mail.thread","mail.activity.mixin"]

    # 7: default method
    @api.model
    def _get_default_date(self):
        return datetime.now() 

    @api.model
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False

    # 8: fields
    name = fields.Char(string="Change Number", readonly=True)
    old_partner_name = fields.Char("Customer Name")
    old_no_stnk = fields.Char("Nomor STNK")
    old_no_bpkb = fields.Char("Nomor BPKB")
    old_no_polisi = fields.Char("Nomor Polisi")
    old_name = fields.Char("Nomor Engine")
    old_chassis_no = fields.Char("Chassis Number")
    old_no_notice = fields.Char("Nomor Notice")
    old_no_faktur = fields.Char("Nomor Faktur")
    old_related_partner_name = fields.Char("Old Customer Name",related='old_partner_name', readonly=True)
    old_related_no_stnk = fields.Char("Old Nomor STNK",related='old_no_stnk', readonly=True)
    old_related_no_bpkb = fields.Char("Old Nomor BPKB",related='old_no_bpkb', readonly=True)
    old_related_no_polisi = fields.Char("Old Nomor Polisi",related='old_no_polisi', readonly=True)
    old_related_name = fields.Char("Old Nomor Engine",related='old_name', readonly=True)
    old_related_chassis_no = fields.Char("Old Chassis Number",related='old_chassis_no', readonly=True)
    old_related_no_notice = fields.Char("Old Nomor Notice",related='old_no_notice', readonly=True)
    old_related_no_faktur = fields.Char("Old Nomor Faktur",related='old_no_faktur', readonly=True)
    new_partner_name = fields.Char(string="New Customer Name")
    new_no_stnk = fields.Char("New Nomor STNK")
    new_no_bpkb = fields.Char("New Nomor BPKB")
    new_no_polisi = fields.Char("New Nomor Polisi")
    new_name = fields.Char("New Nomor Engine")
    new_chassis_no = fields.Char("New Chassis Number")
    new_no_notice = fields.Char("New Nomor Notice")
    new_no_faktur = fields.Char("New Nomor Faktur")
    state = fields.Selection(STATE_SELECTION, string="State", readonly=True, default="draft")
    division = fields.Selection([("Unit","Unit")], "Division", default="Unit",readonly=True)
    date = fields.Datetime("Date", default=_get_default_date)
    confirm_date = fields.Datetime("Confirmed Date")
    note = fields.Text(string="Catatan")

    # 9: relation fields
    company_id = fields.Many2one('res.company', string='Branch', default=_get_default_branch)
    lot_id = fields.Many2one("stock.lot",string="Serial Number", domain=[("state","=","paid")])
    old_partner_id = fields.Many2one("res.partner",string="Customer")
    old_customer_stnk_id = fields.Many2one("res.partner",string="Customer STNK")
    old_related_partner_id = fields.Many2one("res.partner",string ="Old Customer",related='old_partner_id', readonly=True)
    old_related_customer_stnk_id = fields.Many2one("res.partner",string ="Old Customer STNK",related='old_customer_stnk_id', readonly=True)
    new_partner_id = fields.Many2one("res.partner", string="New Customer",)
    new_customer_stnk_id = fields.Many2one("res.partner", string="New Customer STNK",)
    confirm_uid = fields.Many2one('res.users',string="Confirmed by")

    # 10: constraints & sql constraints
    @api.constrains('new_partner_id')
    def _check_new_partner_id(self):
        if self.new_partner_id and self.new_partner_id == self.old_partner_id:
            raise Warning('Perhatian! Data Customer tidak boleh sama dengan data lama')
    @api.constrains('new_customer_stnk_id')
    def _check_new_customer_stnk_id(self):
        if self.new_customer_stnk_id and self.new_customer_stnk_id == self.old_customer_stnk_id:
            raise Warning('Perhatian! Data Customer STNK tidak boleh sama dengan data lama')
    
    @api.constrains('new_partner_name')
    def _check_new_partner_name(self):
        if self.new_partner_name and self.new_partner_name == self.old_partner_name:
            raise Warning('Perhatian! Data Customer Name tidak boleh sama dengan data lama')

    @api.constrains('new_no_stnk')
    def _check_new_no_stnk(self):
        if self.new_no_stnk and self.new_no_stnk == self.old_no_stnk:
            raise Warning('Perhatian! Data Nomor STNK tidak boleh sama dengan data lama')

    @api.constrains('new_no_bpkb')
    def _check_new_no_bpkb(self):
        if self.new_no_bpkb and self.new_no_bpkb == self.old_no_bpkb:
            raise Warning('Perhatian! Data Nomor BPKB tidak boleh sama dengan data lama')

    @api.constrains('new_no_polisi')
    def _check_new_no_polisi(self):
        if self.new_no_polisi and self.new_no_polisi == self.old_no_polisi:
            raise Warning('Perhatian! Data Nomor Polisi tidak boleh sama dengan data lama')

    @api.constrains('new_name')
    def _check_new_name(self):
        if self.new_name and self.new_name == self.old_name:
            raise Warning('Perhatian! Data Nomor Engine tidak boleh sama dengan data lama')

    @api.constrains('new_chassis_no')
    def _check_new_chassis_no(self):
        if self.new_chassis_no and self.new_chassis_no == self.old_chassis_no:
            raise Warning('Perhatian! Data Chassis Number tidak boleh sama dengan data lama')

    @api.constrains('new_no_notice')
    def _check_new_no_notice(self):
        if self.new_no_notice and self.new_no_notice == self.old_no_notice:
            raise Warning('Perhatian! Data Nomor Notice tidak boleh sama dengan data lama')

    @api.constrains('new_no_faktur')
    def _check_new_no_faktur(self):
        if self.new_no_faktur and self.new_no_faktur == self.old_no_faktur:
            raise Warning('Perhatian! Data Nomor Faktur tidak boleh sama dengan data lama')

    # 11: compute/depends & on change methods
    @api.onchange('company_id')
    def _onchange_company_id_for_lot(self):
        self.lot_id = False
        self.old_partner_id = False
        self.old_customer_stnk_id = False
        self.old_partner_name = False
        self.old_no_stnk = False
        self.old_no_bpkb = False
        self.old_no_polisi = False
        self.old_name = False
        self.old_chassis_no = False
        self.old_no_notice = False
        self.old_no_faktur = False


    @api.onchange('company_id','lot_id')
    def _onchange_lot(self):
        if self.company_id and self.lot_id:
            lot = self.lot_id
            self.old_partner_id = lot.partner_id.id
            self.old_partner_name = lot.partner_id.name
            self.old_customer_stnk_id = lot.customer_stnk_id.id
            self.old_no_stnk = lot.vehicle_registration_number
            self.old_no_bpkb = lot.vehicle_ownership_number
            self.old_no_polisi = lot.plate_number
            self.old_name = lot.name
            self.old_chassis_no = lot.chassis_number
            self.old_no_notice = lot.notice_number
            self.old_no_faktur = lot.doc_number

    @api.onchange('new_no_stnk','new_no_bpkb','new_no_polisi')
    def _onchange_new_lot(self):
        if self.new_no_stnk:
            self.new_no_stnk = self.new_no_stnk.upper()
        if self.new_no_bpkb:
            self.new_no_bpkb = self.new_no_bpkb.upper()
        if self.new_no_polisi:
            self.new_no_polisi = self.new_no_polisi.upper()
                        
    @api.onchange('new_name','new_chassis_no')
    def _onchange_kode_mesin(self):
        if not (self.new_name or self.new_chassis_no):
            return
        
        product_id = self.lot_id.product_id if self.lot_id else False
        if not product_id:
            return

        if not product_id.product_tmpl_id.engine_code: 
            self.new_name = False
            raise Warning('Perhatian! Kode Mesin belum terdaftar dalam master Produk!')


        product_kd = product_id.product_tmpl_id.engine_code.replace(' ','')
        pjg = len(product_kd)

        if self.new_name:
            self.new_name = self.new_name.upper()
            if len(self.new_name) != 12:
                self.new_name = False
                raise Warning("Perhatian! Nomor Engine harus 12 Digit")

            if self.is_punctuation(self.new_name):
                self.new_name = False
                raise Warning('Perhatian Engine Number hanya boleh huruf dan angka')

            if product_kd != self.new_name[:pjg]:
                self.new_name = False
                raise Warning('Perhatian Engine Number tidak sesuai dengan Kode Mesin di Produk')

        engine_exist = self.env['stock.lot'].suspend_security().search([('name','=',self.new_name)],limit=1)
        if engine_exist:
            self.new_name = False
            raise Warning('Perhatian Engine Number sudah pernah terdaftar. Silahkan periksa kembali Engine Number yang Anda input.')

        if self.new_chassis_no:
            self.new_chassis_no = self.new_chassis_no.upper()
            check=False
            if self.is_punctuation(self.new_chassis_no):
                self.new_chassis_no = False
                raise Warning('Perhatian Chassis Number hanya boleh huruf dan angka')
                
            if len(self.new_chassis_no) == 14 or (len(self.new_chassis_no) == 17 and self.new_chassis_no[:3] == 'MH1'):
                check=True
            if not check:
                self.new_chassis_no = False
                raise Warning('Chassis Number tidak sesuai format Silahkan periksa kembali Chassis Number yang Anda input')
    
    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        seq_obj = self.env["ir.sequence"]
        for vals in vals_list:
            if not vals.get("name"):
                if vals.get("company_id"):
                    if hasattr(seq_obj,"get_sequence_code"):
                        vals["name"] = seq_obj.get_sequence_code("CL", str(self.env["res.company"].browse(vals["company_id"]).code))
                    else:
                        vals["name"] = seq_obj.next_by_code("tw.vehicle.document.update.data")
            vals['date'] = self._get_default_date()
        
        records = super(TwVehicleDocumentUpdateData,self).create(vals_list)
        return records
    
    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise Warning("Tidak bisa menghapus data berstatus selain draft")
        return super(TwVehicleDocumentUpdateData,self).unlink()
    
    # 13: action methods
    def action_confirm(self):
        for rec in self:
            if not (rec.new_no_stnk or rec.new_name or rec.new_no_bpkb or rec.new_no_polisi or rec.new_chassis_no or rec.new_customer_stnk_id
                    or rec.new_partner_id or rec.new_partner_name or rec.new_no_notice):
                raise Warning("Silahkan pilih minimal 1 data untuk diupdate")
            vals_change_lot ={
                "confirm_uid" : self.env.uid,
                "confirm_date" : fields.Datetime.now() if hasattr(fields,'Datetime') else datetime.now(),
                "date":(self._get_default_date()),
                "state" : "confirm",
            }

            vals_to_update = {}
            message = ''

            if rec.new_partner_id:
                message += "<b>Customer ID  </b>: {} --> {}<br/>".format(
                    (rec.old_partner_id.id if rec.old_partner_id else ''), rec.new_partner_id.id)
                vals_to_update["partner_id"] = rec.new_partner_id.id

            if rec.new_partner_name:
                if rec.new_partner_id:
                    message += "<b>Customer Name</b>: {} --> {}<br/>".format(
                        rec.new_partner_id.name, rec.new_partner_name)
                    rec.new_partner_id.sudo().write({'name': rec.new_partner_name})
                else:
                    message += "<b>Customer Name</b>: {} --> {}<br/>".format(
                        (rec.old_partner_name if rec.old_partner_name else ''), rec.new_partner_name)
                    if rec.old_partner_id:
                        rec.old_partner_id.sudo().write({'name': rec.new_partner_name})

            if rec.new_customer_stnk_id:
                message += "<b>Customer STNK</b>: ID= {}, Name: {} --> ID= {}, Name: {}<br/>".format(
                    (rec.old_customer_stnk_id.id if rec.old_customer_stnk_id else ''),
                    (rec.old_customer_stnk_id.name if rec.old_customer_stnk_id else ''),
                    rec.new_customer_stnk_id.id,
                    rec.new_customer_stnk_id.name)
                vals_to_update["customer_stnk_id"] = rec.new_customer_stnk_id.id

            if rec.new_no_stnk:
                message += "<b>No STNK</b>: {} --> {}<br/>".format((rec.old_no_stnk if rec.old_no_stnk else ''), rec.new_no_stnk)
                vals_to_update["vehicle_registration_number"] = rec.new_no_stnk

            if rec.new_no_bpkb:
                message += "<b>No BPKB</b>: {} --> {}<br/>".format((rec.old_no_bpkb if rec.old_no_bpkb else ''), rec.new_no_bpkb)
                vals_to_update["vehicle_ownership_number"] = rec.new_no_bpkb

            if rec.new_no_polisi:
                message += "<b>No Polisi</b>: {} --> {}<br/>".format((rec.old_no_polisi if rec.old_no_polisi else ''), rec.new_no_polisi)
                vals_to_update["plate_number"] = rec.new_no_polisi

            if rec.new_name:
                message += "<b>No Engine</b>: {} --> {}<br/>".format((rec.old_name if rec.old_name else ''), rec.new_name)
                vals_to_update["name"] = rec.new_name

            if rec.new_chassis_no:
                message += "<b>No Chassis</b>: {} --> {}<br/>".format((rec.old_chassis_no if rec.old_chassis_no else ''), rec.new_chassis_no)
                vals_to_update["chassis_number"] = rec.new_chassis_no

            if rec.new_no_notice:
                message += "<b>No Notice</b>: {} --> {}<br/>".format((rec.old_no_notice if rec.old_no_notice else ''), rec.new_no_notice)
                vals_to_update["notice_number"] = rec.new_no_notice

            if rec.new_no_faktur:
                message += "<b>No Faktur</b>: {} --> {}<br/>".format((rec.old_no_faktur if rec.old_no_faktur else ''), rec.new_no_faktur)
                vals_to_update["doc_number"] = rec.new_no_faktur

            # write to lot if any update
            if vals_to_update and rec.lot_id:
                rec.lot_id.sudo().write(vals_to_update)
            if message:
                rec.message_post(body=Markup("Perubahan Data :<br/>%s" % message), subtype_xmlid="mail.mt_note")

            rec.write(vals_change_lot)
        return True
    
    def action_open_vehicle_document(self):
        self.ensure_one()
        lot = self.env['stock.lot'].sudo().search([('customer_stnk_id', '=', self.new_customer_stnk_id.id)],limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicle Document',
            'res_model': 'stock.lot',
            'view_mode': 'form',
            'view_id': self.env.ref('tw_vehicle_document.tw_udstk_view_form').id,
            'res_id': lot.id,  
            'target': 'current',
        }

    # 14: private methods
    def is_punctuation(self,words):
        for n in range(len(words)):
            if words[n] in string.punctuation:
                return True
        return False
    
    def _action_request(self):
        for rec in self:
            if not (rec.new_no_stnk or rec.new_name or rec.new_no_bpkb or rec.new_no_polisi or rec.new_chassis_no or rec.new_customer_stnk_id
                    or rec.new_partner_id or rec.new_partner_name or rec.new_no_notice or rec.new_no_faktur):
                raise Warning("Silahkan pilih minimal 1 data untuk diupdate")
        return True