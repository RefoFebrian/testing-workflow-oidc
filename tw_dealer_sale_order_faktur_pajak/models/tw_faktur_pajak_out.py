from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class InheritFakturPajakOut(models.Model):
    _inherit = "tw.faktur.pajak.out"


    def _get_faktur_pajak_lines_from_source(self, record):
        """ Override helper untuk menambahkan logika DSO """
        model_name = record._name
        
        if model_name == 'tw.dealer.sale.order':
            lines = []
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
                    'ppn': dpp * tax_amount,
                    'total_discount': discount,
                    'qty': line.product_uom_qty,
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'product_uom_id': line.product_uom.id,
                }))
            
            return lines  # Return lines for DSO

        return super()._get_faktur_pajak_lines_from_source(record)


    def _prepare_faktur_pajak_vals(self, record):
        """
        Mempersiapkan dictionary nilai untuk pembuatan Faktur Pajak
        berdasarkan model dari record sumber. Metode ini berisi semua logika
        spesifik untuk setiap model.
        """

        vals = super()._prepare_faktur_pajak_vals(record)

        if record._name == 'tw.dealer.sale.order':
            lines = []
            for line in record.order_line:
                # disc_cust = sum(line.discount_line.mapped('discount_customer'))
                # TODO: Check apakah voucher sudah di migrasi kan ke Teto
                # amount_program = sum(line.voucher_line_ids.mapped('diskon_voucher'))
                tax_amount = line.tax_id.amount or 0.0
                tax_divisor = 1 + tax_amount

                # (line.price_unit - (disc_cust + (line.discount_regular - amount_program))),
                # if line.is_bbn == 'Y':
                #     dpp_components = (
                #         (line.price_unit - (0 + (line.discount_regular))),
                #         line.bbn_serv_amount,
                #         (line.bbn_serv_amount * tax_amount),
                #         (line.bbn_amount - line.bbn_force_cogs)
                #     )
                #     dpp = sum(dpp_components) / tax_divisor
                # else:
                    # dpp = (line.price_unit - (line.discount_total - amount_program)) * line.product_qty / tax_divisor
                
                dpp = (line.price_unit - (0)) * line.product_qty / tax_divisor

                harga_total = round(
                    ((line.price_unit / tax_divisor)) * line.product_qty
                )
                discount = harga_total - dpp
                
                lines.append((0, 0, {
                    'kode_barang': line.product_id.get_kode_barang_pajak(),
                    'uom': line.product_id.get_uom_pajak(),
                    'amount': line.price_unit * line.product_qty,
                    # 'untaxed_amount': dpp,
                    'untaxed_amount': dpp * line.tax_id.tax_base_amount,
                    'ppn': dpp * tax_amount,
                    'total_discount': discount,
                    'qty': line.product_qty,
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'product_uom_id': line.product_uom.id
                }))
            vals.update({
                'partner_id': record.partner_id.id,
                'company_id': record.company_id.id,
                'date': record.date_order,
                'amount_total': record.amount_total,
                'untaxed_amount': record.amount_untaxed,
                'tax_amount': record.amount_tax,
                'line_ids': lines,
                'ref': record.name,
            })
        
        return vals