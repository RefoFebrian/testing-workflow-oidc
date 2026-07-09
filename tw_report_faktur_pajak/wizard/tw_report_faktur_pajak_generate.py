from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class TWReportFakturPajakGenerate(models.TransientModel):
    _inherit = "tw.report.faktur.pajak"

    def _print_excel_report_generate_faktur_pajak(self):
        query_where = "WHERE 1=1"

        if self.thn_penggunaan:
            query_where += " AND EXTRACT(YEAR FROM gfp.date)= %s" % self.thn_penggunaan
        if self.start_date:
            query_where += " AND gfp.date >= '%s'" % self.start_date
        if self.end_date:
            query_where += " AND gfp.date <= '%s'" % self.end_date
        if self.state_generate_faktur_pajak:
            query_where += " AND gfp.state = '%s'" % self.state_generate_faktur_pajak
        if self.company_ids:
            query_where += f" AND gfp.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            companies = self.env.user._get_company_ids()
            query_where += f" AND gfp.company_id IN {str(tuple(companies)).replace(',)', ')')}"
        
        query = """
            SELECT 
                gfp.name AS generate_ref,
                gfp.origin AS no_document,
                pajak.total AS total_generated
            FROM tw_faktur_pajak gfp
                INNER JOIN tw_faktur_pajak_out fp ON fp.faktur_pajak_id = gfp.id 
                LEFT JOIN (SELECT faktur_pajak_id,count(id) as total FROM tw_faktur_pajak_out GROUP BY faktur_pajak_id) pajak ON pajak.faktur_pajak_id = gfp.id           
            %s
            ORDER BY gfp.name,gfp.date
        """ % query_where

        query_sheet_2 = """
            SELECT 
                gfp.name AS generate_ref,
                gfp.origin AS no_document,
                gfp.date::Text AS date,
                EXTRACT(YEAR FROM gfp.date)::Text AS tahun_penggunaan,
                gfp.release_date::Text AS tgl_terbit,
                gfp.counter_start AS counter_start,
                gfp.counter_end AS counter_end,
                gfp.prefix AS prefix,
                gfp.padding::Text AS padding,
                gfp.state AS state,
                fp.name AS code_faktur_pajak,
                fp.state AS state,
                pajak.total AS total_generated
            FROM tw_faktur_pajak gfp
                INNER JOIN tw_faktur_pajak_out fp ON fp.faktur_pajak_id = gfp.id 
                LEFT JOIN (SELECT faktur_pajak_id,count(id) as total FROM tw_faktur_pajak_out GROUP BY faktur_pajak_id) pajak ON pajak.faktur_pajak_id = gfp.id           
            %s
            ORDER BY gfp.name,gfp.date
        """ % query_where

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        self.env.cr.execute(query_sheet_2)
        ress_2 = self.env.cr.dictfetchall()

        if not ress or not ress_2:
            raise Warning('Data tidak ada...')

        return ress, ress_2