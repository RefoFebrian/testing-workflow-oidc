# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import datetime

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockLot(models.Model):
    _inherit = "stock.lot"
    
    # 7: defaults methods
    def _get_year(self):
        current_year = datetime.now().year
        start_year = 2000
        years_available = []

        for x in reversed(range(start_year, current_year + 1)):
            elem = ("{}".format(x), "{}".format(x))
            years_available.append(elem)

        return years_available

    # 8: fields
    chassis_number = fields.Char(string='Nomor Rangka', help='Nomor Rangka Kendaraan')
    # TODO: Pindahkan plate_number vke document handling (karena ini kebutuhan STNK/BPKB)
    plate_number = fields.Char(string='No Polisi', help='Nomor Polisi Kendaraan')
    production_year = fields.Selection(_get_year,'Tahun Produksi', help='Tahun Produksi Kendaraan')
    ready_for_sale = fields.Selection([
        ('good','Good'),
        ('not_good','Not Good')
    ],'Ready For Sale')
    state = fields.Selection([
        ('intransit', 'Intransit'),
        ('titipan','Titipan'),
        ('stock', 'Stock'), 
        ('reserved','Reserved'),
        ('sold','Sold'), 
        ('paid', 'Paid'),
        ('sold_offtr','Sold.offtr'),
        ('paid_offtr','Paid.offtr'),
        ('workshop','Workshop'),
        ('cancelled','Cancel')
    ],string='Status',help='Status Kendaraan')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    receive_date = fields.Datetime(string='Receive Date ',help='Tanggal Penerimaan MD')

    # 9: relation fields
    company_id = fields.Many2one("res.company", string="Branch")
    initial_company_id = fields.Many2one("res.company", string="Initial Branch")
    supplier_id = fields.Many2one(comodel_name='res.partner', string="Supplier")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer Pemilik', tracking=True, required=False)
    batch_transfer_id = fields.Many2one(comodel_name='stock.picking.batch', string='Batch Transfer')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('company_id'):
                vals['initial_company_id'] = vals['company_id']
            if vals.get('product_id'):
                product = self.env['product.product'].browse(vals['product_id'])
                categ = product.categ_id
                if categ.serial_number_length > 0 and categ.serial_number_length != len(vals.get('name', '')):
                    raise Warning(_('Serial Number %s harus %s digit!'%(vals.get('name'), categ.serial_number_length)))
                    
                chassis_number = vals.get('chassis_number', '')
                if categ.tracking == 'serial_chassis' and chassis_number and categ.chassis_number_length > 0 and categ.chassis_number_length != len(chassis_number):
                    raise Warning(_('Chassis Number %s harus %s digit!' % (chassis_number, categ.chassis_number_length)))

        return super(InheritStockLot, self).create(vals_list)
    
    def write(self,vals):
        if 'company_id' in vals:
            for lot in self:
                if lot.location_id.company_id and vals['company_id'] and lot.location_id.company_id.id != vals['company_id']:
                    raise Warning(_("You cannot change the company of a lot/serial number currently in a location belonging to another company."))
        
        #? NOTE : Call the super of the parent class (models.Model) to bypass stock.lot's write method
        #? Tidak memanggil super() karena ada validasi untuk tidak mengubah produk di lot bawaan
        #? sedangkan untuk Bundling, produk harus di ubah menggunakan lot yang sama.
        #? silahkan inherit method _prepare_write_vals untuk memodifikasi vals.
        #? dan _process_after_write untuk melakukan sesuatu setelah write.
        vals = self._prepare_write_vals(vals)
        write =  super(models.Model, self).write(vals) #? Jangan di ubah, penjelasan ada di note di atas
        self._process_after_write(vals)
        return write 
    
    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_stock.group_tw_stock_lot_form_read'):
            raise Warning(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res

    # 13: action methods

    # 14: private methods
    def _prepare_write_vals(self,vals):
        return vals
    
    def _process_after_write(self,vals):
            for lot in self:
                if vals.get('company_id'):
                    if not lot.initial_company_id:
                        lot.initial_company_id = lot.company_id
                if vals.get('name'):
                    # Skip validation
                    if self.env.context.get('skip_serial_length_check'):
                        continue
                    if lot.product_id.categ_id.serial_number_length:
                        if lot.product_id.categ_id.serial_number_length != len(lot.name):
                            raise Warning(_('Serial Number %s harus %s digit!'%(lot.name, lot.product_id.categ_id.serial_number_length)))

