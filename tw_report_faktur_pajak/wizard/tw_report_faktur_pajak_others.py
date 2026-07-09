from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class TWReportFakturPajakOthers(models.TransientModel):
    _inherit = "tw.report.faktur.pajak"

    def _print_excel_report_faktur_pajak_others(self):
        query_where = " "

        if self.start_date:
            query_where += " AND fpo.date >= '%s'" % self.start_date
        if self.end_date:
            query_where += " AND fpo.date <= '%s'" % self.end_date
        if self.pajak_gabungan:
            query_where += " AND fpo.pajak_gabungan = true"
        if self.state_other_faktur_pajak:
            query_where += " AND fpo.state = '%s'" % self.state_other_faktur_pajak
        if self.thn_penggunaan:
            query_where += " AND EXTRACT(YEAR FROM fpo.date)= %s" % self.thn_penggunaan
        if self.partner_ids:
            query_where += " AND p.id in %s" % str(tuple(self.partner_ids.ids)).replace(',)', ')')
        if self.company_ids:
            query_where += f" AND fpo.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            companies = self.env.user._get_company_ids()
            query_where += f" AND fpo.company_id IN {str(tuple(companies)).replace(',)', ')')}"

        query = """
            select 
            fpo.name as reference, 
            fp.name as no_faktur,
            p.code as partner_code, 
            p.name as partner_name,
            fpo.date::Text as date,
            fpo.pajak_gabungan::Text as pajak_gabungan,
            fpo.thn_penggunaan::Text as thn_penggunaan,
            fpo.tgl_terbit::Text as tgl_terbit,
            fpo.kwitansi_no as no_kwitansi,
            fpo.untaxed_amount as untaxed_amount,
            fpo.total_amount as amount_total,
            fpo.tax_amount as tax_amount,
            fpo.state as state
            from tw_faktur_pajak_other fpo
            inner join tw_faktur_pajak_out fp ON fp.id = fpo.faktur_pajak_out_id
            inner join res_partner p ON p.id = fpo.partner_id
            where fpo.id is not null %s
            ORDER BY fpo.name , fpo.id
        """ % query_where

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        if not ress:
            raise Warning('Data tidak ada...')

        return ress