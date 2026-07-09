# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class StockPickingExpeditionInherit(models.Model):
    _inherit = "stock.picking"
    
    # 7: defaults methods

    # 8: fields
    delivery_state = fields.Selection([
        ('draft', 'Draft'),
        ('intransit', 'Intransit'),
        ('delivered', 'Delivered')
    ], string="Delivery State", default='draft', help="Delivery state of the stock picking.")
    assign_driver_date = fields.Datetime(string="Assign Driver Date", help="Assign driver date of the stock picking.")
    assign_driver_uid = fields.Many2one('res.users', string="Assign Delivery By", help="User who is responsible for the delivery.")
    intransit_date = fields.Datetime(string="Intransit Date", help="Intransit date of the stock picking.")
    intransit_uid = fields.Many2one('res.users', string="Intransit By", help="User who is responsible for the intransit.")
    delivery_date = fields.Datetime(string="Delivery Date", help="Delivery date of the stock picking.")
    delivery_driver_id = fields.Many2one('hr.employee', string="Delivery Driver", help="Employee who is responsible for the delivery.")
    
    file_image = fields.Binary(string="File Image", help="File image for the delivery picking.")
    filename_upload_image = fields.Char(string="Filename Upload Image", help="Filename for the uploaded image.")
    file_image_show = fields.Binary(string="File Image Show", compute='_compute_file', help="Image show for the delivery picking.")

    file_travel_document = fields.Binary(string="File Surat Jalan", help="File Surat Jalan for the delivery picking.")
    filename_upload_travel_document = fields.Char(string="Filename Upload Surat Jalan", help="Filename for the uploaded Surat Jalan.")
    file_travel_document_show = fields.Binary(string="File Surat Jalan Show", compute='_compute_file', help="Surat Jalan show for the delivery picking.")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('filename_upload_image', 'filename_upload_travel_document')
    def _compute_file(self):
        self.file_image_show = False
        self.file_travel_document_show = False
        if self.filename_upload_image:
            file = self.env['tw.config.files'].suspend_security().get_file(self.filename_upload_image)
            self.file_image_show = file
        if self.filename_upload_travel_document:
            file = self.env['tw.config.files'].suspend_security().get_file(self.filename_upload_travel_document)
            self.file_travel_document_show = file

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        file_image = []
        file_travel_document = []
        for vals in vals_list:
            if vals.get('file_image'):
                file_image.append(vals['file_image'])
                vals['file_image'] = False
            if vals.get('file_travel_document'):
                file_travel_document.append(vals['file_travel_document'])
                vals['file_travel_document'] = False
        
        create_list = super(StockPickingExpeditionInherit, self).create(vals_list)
        for n, create in enumerate(create_list):
            if file_image and file_image[n]:
                tmp_file = vals['filename_upload_image'].split('.')
                filename_up = 'picture_expedition_' + str(create.id) + '.' + tmp_file[len(tmp_file) - 1]
                self.env['tw.config.files'].suspend_security().upload_file(filename_up, file_image[n])
                self.check_size_file(filename_up)
                create.filename_upload_image = filename_up

            if file_travel_document and file_travel_document[n]:
                tmp_file = vals['filename_upload_travel_document'].split('.')
                filename_up = 'travel_document_' + str(create.id) + '.' + tmp_file[len(tmp_file) - 1]
                self.env['tw.config.files'].suspend_security().upload_file(filename_up, file_travel_document[n])
                self.check_size_file(filename_up)
                create.filename_upload_travel_document = filename_up
        return create_list
    
    def write(self, vals):
        if vals.get('file_image'):
            file = vals['file_image']
            vals['file_image'] = False
            tmp_file = vals['filename_upload_image'].split('.')
            filename_up = 'picture_expedition_' + str(self.id) + '.' + tmp_file[len(tmp_file) - 1]
            self.env['tw.config.files'].suspend_security().upload_file(filename_up, file)
            self.check_size_file(filename_up)
            vals['filename_upload_image'] = filename_up
            vals['delivery_state'] = 'delivered'
        if vals.get('file_travel_document'):
            file = vals['file_travel_document']
            vals['file_travel_document'] = False
            tmp_file = vals['filename_upload_travel_document'].split('.')
            filename_up = 'travel_document_' + str(self.id) + '.' + tmp_file[len(tmp_file) - 1]
            self.env['tw.config.files'].suspend_security().upload_file(filename_up, file)
            self.check_size_file(filename_up)
            vals['filename_upload_travel_document'] = filename_up
        return super(StockPickingExpeditionInherit, self).write(vals)

    # 13: action methods
    def action_assign_delivery_driver(self):
        """Open Assign Delivery Driver wizard with selected picking records pre-filled."""
        divisions = set(self.mapped('division'))
        if len(divisions) > 1:
            raise Warning(
                _("Tidak dapat assign delivery driver karena picking yang dipilih berbeda division: [%s]. "
                  "Harap pilih picking dengan division yang sama.") % ', '.join(str(d) for d in divisions)
            )
        form_id = self.env.ref('tw_expedition_apps.tw_assign_delivery_driver_wizard_view').id
        return {
            'name': 'Assign Delivery Driver',
            'res_model': 'tw.assign.delivery.driver.wizard',
            'type': 'ir.actions.act_window',
            'views': [(form_id, 'form')],
            'target': 'new',
            'context': {
                'default_picking_ids': self.ids,
                'default_division': divisions.pop() if len(divisions) == 1 else False,
            },
        }

    # 14: private methods
    def check_size_file(self, filename):
        check_size = self.env['tw.config.files'].suspend_security().cek_size(filename)
        if check_size > 5000000:
            raise Warning(f"Perhatian!\nUkuran File '{filename}' Melebihi Maksimal, File Pendukung Maks Size 5MB")
    
