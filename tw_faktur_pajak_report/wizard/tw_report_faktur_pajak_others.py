# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models
from odoo.exceptions import UserError as Warning

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TWReportFakturPajakOthers(models.TransientModel):
    """Extension for Faktur Pajak Others report."""

    _inherit = "tw.report.faktur.pajak"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _print_excel_report_faktur_pajak_others(self):
        """Generate Faktur Pajak Others report data."""
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
            query_where += " AND EXTRACT(YEAR FROM fpo.date) = %s" % self.thn_penggunaan
        if self.partner_ids:
            query_where += " AND p.id in %s" % str(tuple(self.partner_ids.ids)).replace(',)', ')')

        if self.company_ids:
            query_where += f" AND fpo.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND fpo.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        query = """
            SELECT
                fpo.name AS reference,
                fp.name AS no_faktur_pajak,
                p.code AS partner_code,
                p.name AS partner_name,
                fpo.date::Text AS date,
                fpo.pajak_gabungan::Text AS pajak_gabungan,
                fpo.thn_penggunaan::Text AS tahun_penggunaan,
                fpo.tgl_terbit::Text AS tanggal_terbit,
                fpo.kwitansi_no AS no_kwitansi,
                fpo.untaxed_amount AS untaxed_amount,
                fpo.tax_amount AS tax_amount,
                fpo.total_amount AS amount_total,
                fpo.state AS state
            FROM tw_faktur_pajak_other fpo
                INNER JOIN tw_faktur_pajak_out fp ON fp.id = fpo.faktur_pajak_out_id
                INNER JOIN res_partner p ON p.id = fpo.partner_id
            WHERE fpo.id IS NOT NULL %s
            ORDER BY fpo.name, fpo.id
        """ % query_where

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        if not ress:
            raise Warning('Data tidak ada...')

        return ress
