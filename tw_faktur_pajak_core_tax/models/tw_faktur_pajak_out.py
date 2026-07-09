# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
import logging
import ast

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

_logger = logging.getLogger(__name__)

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class InheritFakturPajakOut(models.Model):
    """Extend tw.faktur.pajak.out dengan logic Coretax."""

    _inherit = "tw.faktur.pajak.out"

    # 9: Relation Fields
    line_ids = fields.One2many('tw.faktur.pajak.out.line', 'faktur_pajak_out_id')

    # 10: Private Method

    def _check_implementation(self):
        """Cek apakah sistem menggunakan format Coretax."""
        # Menggunakan ast.literal_eval agar bisa menangani "True" (string) atau True (boolean)
        # dan mengubahnya menjadi boolean yang benar untuk perbandingan.
        use_coretax_param = self.env['ir.config_parameter'].sudo().get_param(
            'tw_faktur_pajak_core_tax.use_coretax', default=False
        )
        return ast.literal_eval(str(use_coretax_param))

    def get_number_faktur_pajak(self, transaction):
        """
        Routing method: menentukan apakah menggunakan old format atau Coretax.
        Di-override dari base module melalui _inherit.

        Jika config use_coretax aktif → create_faktur_pajak (Coretax).
        Jika tidak → get_number_of_faktur_pajak (Old format, assign nomor).

        :param transaction: recordset dari dokumen sumber (e.g., sale.order).
        :return: recordset tw.faktur.pajak.out.
        """
        if not transaction:
            raise Warning("Transaction not found!")

        is_use_coretax = self._check_implementation()
        if is_use_coretax:
            return self.create_faktur_pajak(transaction)
        else:
            return self.get_number_of_faktur_pajak(transaction._name, transaction.id)

    @api.model
    def create_faktur_pajak(self, record):
        """
        Membuat record Faktur Pajak (FPO) dari berbagai dokumen sumber.
        Ini adalah core method yang menjadi entry point, memanggil helper
        untuk mempersiapkan data sebelum membuat record. Core Tax Implementation

        :param record: recordset dari dokumen sumber (e.g., sale.order).
        :return: recordset dari faktur.pajak yang baru dibuat.
        """
        
        ref_name = getattr(record, 'name', False) or getattr(record, 'number', False)
        if not ref_name:
            _logger.error(f"Record {record._name} (ID: {record.id}) tidak memiliki field 'name' atau 'number'.")
            return self.env['faktur.pajak']
                
        existing_fpo = self.search([('ref', '=', ref_name)], limit=1)
        if existing_fpo:
            raise Warning(f"Faktur Pajak untuk referensi '{ref_name}' sudah ada (ID: {existing_fpo.id}). Proses dihentikan.")
        
        final_vals = self._prepare_faktur_pajak_vals(record)
        if not final_vals:
            raise Warning(f"Pembuatan Faktur Pajak Otomatis tidak didukung untuk model: '{record._name}'.")
        
        fpo = self.create(final_vals)
        record.write({'faktur_pajak_out_id': fpo.id})
        
        return fpo

    
    def _get_faktur_pajak_lines_from_source(self, record):
        """
        HELPER: Method ini hanya fokus mengekstrak DETAIL BARIS
        dari berbagai model sumber.
        """
        model_name = record._name
        lines = []

        if model_name == 'tw.work.order':
            for line in record.order_line:
                tax_amount = line.tax_id.amount or 0.0
                tax_divisor = 1 + tax_amount
                qty = line.qty_delivered if line.division == 'Sparepart' else line.product_uom_qty
                
                dpp = round(line.price_unit / tax_divisor * qty * (1 - (line.discount / 100)))
                harga_total = round(line.price_unit / tax_divisor * qty)
                discount = harga_total - dpp

                lines.append((0, 0, {
                    'kode_barang': line.product_id.get_kode_barang_pajak(),
                    'uom': line.product_id.get_uom_pajak(),
                    'amount': round(line.price_unit / tax_divisor),
                    'untaxed_amount': dpp,
                    # 'dpp': dpp * line.tax_id.tax_base_amount, #TODO: Error karena fields tidak ada, dicomment sementara untuk testing WO
                    'ppn': dpp * tax_amount,
                    'total_discount': line.discount,
                    'qty': qty,
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'product_uom_id': line.product_uom.id
                }))
            
        elif model_name == 'sale.order':
            for line in record.order_line:
                tax_amount = line.tax_id.amount or 0.0
                tax_divisor = 1 + tax_amount

                dpp = (line.price_unit * (1 - line.discount / 100) / tax_divisor) * line.product_uom_qty
                harga_total = round((line.price_unit / tax_divisor) * line.product_uom_qty)
                discount = harga_total - dpp
                
                lines.append((0, 0, {
                    'kode_barang': line.product_id.get_kode_barang_pajak(),
                    'uom': line.product_id.get_uom_pajak(),
                    'amount': line.price_unit / tax_divisor,
                    'untaxed_amount': dpp,
                    # 'dpp': dpp * line.tax_id.tax_base_amount, #TODO: Error karena fields tidak ada, dicomment sementara untuk testing WO
                    'ppn': dpp * tax_amount,
                    'total_discount': discount,
                    'qty': line.product_uom_qty,
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'product_uom_id': line.product_uom.id,
                }))
           

        elif model_name == 'tw.disposal.asset':
            ppn = record.amount_tax
            lines.append((0, 0, {
                'kode_barang': 'B',
                'uom': 'UM.0033',
                'amount': record.amount_total,
                'untaxed_amount': record.amount_untaxed,
                # 'dpp': record.untaxed_amount, #TODO: Error karena fields tidak ada, dicomment sementara untuk testing WO
                'ppn': ppn,
                'qty': 1,
                'tax_ids': [(6, 0, record.disposal_line_sold_ids[0].tax_id.ids)],
                'product_name': record.name,
            }))
            

        elif model_name == 'tw.account.payment':
            ppn = record.tax_amount
            lines.append((0, 0, {
                'kode_barang': 'B',
                'uom': 'UM.0033',
                'amount': record.amount,
                'untaxed_amount': record.untaxed_amount,
                # 'dpp': record.untaxed_amount, #TODO: Error karena fields tidak ada, dicomment sementara untuk testing WO
                'ppn': ppn,
                'qty': 1,
                'tax_ids': [(6, 0, record.line_cr_ids[0].tax_id.ids)],
                'product_name': record.name,
            }))

        return lines

    def _prepare_faktur_pajak_vals(self, record):
        """
        Mempersiapkan dictionary nilai untuk pembuatan Faktur Pajak
        berdasarkan model dari record sumber. Metode ini berisi semua logika
        spesifik untuk setiap model.
        """
        if not record:
            raise Warning("Please Install sub module of Core Tax in severals modules with Core Tax")
        model_name = record._name
        vals = {}
        # PANGGIL HELPER BARU UNTUK MENDAPATKAN DETAIL BARIS
        lines = self._get_faktur_pajak_lines_from_source(record)
        
        if model_name in ['tw.work.order', 'sale.order', 'tw.disposal.asset', 'tw.account.payment']:
             vals = {
                'partner_id': record.partner_id.id if hasattr(record, 'partner_id') else record.customer_id.id,
                'company_id': record.company_id.id,
                'date': getattr(record, 'date_order', getattr(record, 'date', False)),
                'amount_total': record.amount_total if hasattr(record, 'amount_total') else record.amount,
                'untaxed_amount': record.amount_untaxed if hasattr(record, 'amount_untaxed') else record.untaxed_amount,
                'tax_amount': record.amount_tax if hasattr(record, 'amount_tax') else record.tax_amount,
                'ref': getattr(record, 'name', getattr(record, 'number', False)),
            }

        model_id = self.env['ir.model']._get(model_name).id
        vals.update({
            'model_id': model_id,
            'transaction_id': record.id,
            'state': 'open',
            'company_id': record.company_id.id or self.env.company.id,
            'line_ids': lines,  # Masukkan detail baris yang didapat dari helper
        })
        
        return vals