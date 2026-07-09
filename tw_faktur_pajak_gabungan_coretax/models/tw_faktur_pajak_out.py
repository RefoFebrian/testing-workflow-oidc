from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class InheritFakturPajakOut(models.Model):
    _inherit = "tw.faktur.pajak.out"

    def _get_faktur_pajak_lines_from_source(self, record):
        """ 
        Override helper untuk menambahkan logika FPG.
        Logika ini akan memanggil dirinya sendiri secara rekursif!
        """
        model_name = record._name
        
        if model_name == 'tw.faktur.pajak.gabungan':
            all_lines = []
            for fpg_line in record.pajak_gabungan_line:
                source_doc = self.env[fpg_line.model].search(
                    [('name', '=', fpg_line.name)], limit=1
                )
                if not source_doc:
                    continue
                
                source_lines = self._get_faktur_pajak_lines_from_source(source_doc)
                
                all_lines.extend(source_lines)
                
            return all_lines
            
        return super()._get_faktur_pajak_lines_from_source(record)

    def _prepare_faktur_pajak_vals(self, record):
        """ Override header untuk menambahkan header FPG """
        vals = super()._prepare_faktur_pajak_vals(record)
        
        if record._name == 'tw.faktur.pajak.gabungan':
            vals.update({
                'partner_id': record.partner_id.id,
                'company_id': record.company_id.id,
                'date': record.date_pajak or record.date,
                'amount_total': sum(record.pajak_gabungan_line.mapped('total_amount')),
                'untaxed_amount': sum(record.pajak_gabungan_line.mapped('untaxed_amount')),
                'tax_amount': sum(record.pajak_gabungan_line.mapped('tax_amount')),
                'ref': record.name,
                'is_combined_tax': True,
            })
        
        return vals