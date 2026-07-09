# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwProcessOffTheRoadLine(models.Model):
    _name = "tw.process.off.the.road.line"
    _description = "Pengurusan STNK BPKB Line"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now().strftime('%Y-%m-%d')

    # 8: fields

    # 9: relation fields
    lot_id = fields.Many2one('stock.lot',string='No Engine')
    available_lot_ids = fields.Many2many('stock.lot', string='Domain Lot', compute='_compute_available_lot_ids')
    plate_id = fields.Many2one(comodel_name='tw.selection', string='Plate', domain=[('type', '=', 'PlateType')])
    process_offtr_id = fields.Many2one('tw.process.off.the.road',string='Penerimaan Notice')
    customer_stnk_id = fields.Many2one('res.partner',related="lot_id.customer_stnk_id",string="Customer STNK",readonly=True)

    # 10: constraints & sql constraints
    @api.constrains('lot_id', 'process_offtr_id')
    def _check_unique_lot_id_process_offtr_id(self):
        for record in self:
            if self.search(
                [('lot_id', '=', record.lot_id.id),
                ('process_offtr_id', '=', record.process_offtr_id.id),
                ('id', '!=', record.id)]):
                raise Warning(_("Detail Engine duplicate pada Proses STNK BPKB %s, silahkan cek kembali !")%(record.process_offtr_id.name))

    # 11: compute/depends & on change methods
    @api.onchange('lot_id','process_offtr_id.partner_id','plate','process_offtr_id.company_id')
    def onchange_engine(self):
        if self.lot_id :
            lot_obj = self.env['stock.lot'].search([
                ('id','=',self.lot_id.id)
            ])
            if lot_obj:   
                biro_line = self._get_harga_bbn_detail(self.plate_id,lot_obj.product_id.product_tmpl_id,self.process_offtr_id.company_id) 
                if not biro_line :
                    raise Warning(_("Perhatian !\nData Pricelist BBN tidak ditemukan untuk produk engine %s, silahkan konfigurasi data cabang dulu. ! ")%(lot_obj.lot_id))
                self.customer_stnk_id = lot_obj.customer_stnk_id.id       

    @api.onchange('lot_id','process_offtr_id.partner_id','plate','process_offtr_id.company_id')
    def onchange_plate(self):
        if self.lot_id:     
            lot_obj = self.env['stock.lot'].search([
                ('id','=',self.lot_id.id)
            ])
            if lot_obj:   
                biro_line = self._get_harga_bbn_detail(self.plate_id, lot_obj.product_id.product_tmpl_id,self.process_offtr_id.company_id) 
                if not biro_line :
                    raise Warning(_("Perhatian !\nData Pricelist BBN tidak ditemukan untuk produk engine %s, silahkan konfigurasi data cabang dulu. ! ")%(lot_obj.lot_id))

    @api.depends('process_offtr_id.company_id', 'process_offtr_id.customer_id')
    def _compute_available_lot_ids(self):
        for record in self:
            record.available_lot_ids = False
            domain = [
                ('vehicle_document_receive_date', '!=', False),
                ('process_otr_date', '=', False),
                ('document_state', '=', 'document_receive'),
                ('company_id', '=', record.process_offtr_id.company_id.id),
                '|',
                ('state', '=', 'sold_offtr'),
                ('state', '=', 'paid_offtr')
            ]

            if record.process_offtr_id.customer_id:
                domain.append(('customer_stnk_id', '=', record.process_offtr_id.customer_id.id))

            record.available_lot_ids = self.env['stock.lot'].search(domain)

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_harga_bbn_detail(self, plate, product_template_id,branch_id):
        pricelist_obj = self.env['product.pricelist']
        pricelist_bbn_sales_id = pricelist_obj._get_bbn_sales_pricelist(branch_id, plate)
        if not pricelist_bbn_sales_id:
            raise Warning(_("Perhatian !\nPricelist BBN Sales tidak ditemukan"))
        return pricelist_bbn_sales_id.with_company(branch_id.id)._price_get(product_template_id,1)[pricelist_bbn_sales_id.id]
