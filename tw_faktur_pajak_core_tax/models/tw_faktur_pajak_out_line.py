from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class TwFakturPajakOutLine(models.Model):
    _name = "tw.faktur.pajak.out.line"
    _description = "TW Faktur Pajak Out Line"

    # 9: Fields
    product_name = fields.Char(string='Deskripsi')
    qty = fields.Float(string='Qty')
    amount = fields.Float(string='Harga Satuan')
    total_discount = fields.Float(string='Diskon')
    untaxed_amount = fields.Float(string='DPP')
    ppn = fields.Float(string='PPN')
    kode_barang = fields.Char(string='Kode Barang Pajak')
    uom = fields.Char(string='UoM Pajak')
    
    # 10: Relation Fields
    faktur_pajak_out_id = fields.Many2one('tw.faktur.pajak.out', string="Faktur Pajak", ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_id = fields.Many2one('uom.uom', string='UoM')
    tax_ids = fields.Many2many('account.tax','tw_faktur_pajak_out_line_account_tax_rel', 'tw_faktur_pajak_out_line_id', 'account_tax_id', string='Tax')