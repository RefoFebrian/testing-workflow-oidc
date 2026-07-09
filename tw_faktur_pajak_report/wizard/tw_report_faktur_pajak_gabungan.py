# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models
from odoo.exceptions import UserError as Warning

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TWReportFakturPajakGabungan(models.TransientModel):
    """Extension for Faktur Pajak Gabungan report."""

    _inherit = "tw.report.faktur.pajak"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _print_excel_report_faktur_pajak_gabungan(self):
        """Generate Faktur Pajak Gabungan report data."""
        query_where = " "

        if self.company_ids:
            query_where += f" AND fpg.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND fpg.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.partner_ids:
            query_where += " AND fpg.partner_id in %s" % str(tuple(self.partner_ids.ids)).replace(',)', ')')
        if self.start_date:
            query_where += " AND fpg.date >= '%s'" % str(self.start_date)
        if self.end_date:
            query_where += " AND fpg.date <= '%s'" % str(self.end_date)
        if self.division:
            query_where += " AND fpg.division = '%s'" % str(self.division)
        if self.state_gabungan_faktur_pajak:
            query_where += " AND fpg.state = '%s'" % str(self.state_gabungan_faktur_pajak)

        query = """
            SELECT
                fpg.name AS transaction_ref,
                p.name AS partner,
                t.sum_taxed_amount AS total_tax,
                t.sum_untaxed_amount AS total_untaxed,
                t.sum_total_amount AS grand_total
            FROM tw_faktur_pajak_gabungan fpg
                LEFT JOIN res_company b ON b.id = fpg.company_id
                LEFT JOIN tw_faktur_pajak_out fp ON fp.id = fpg.faktur_pajak_out_id
                LEFT JOIN res_partner p ON p.id = fpg.partner_id
                LEFT JOIN tw_faktur_pajak_gabungan_line l ON l.pajak_gabungan_id = fpg.id
                LEFT JOIN ir_model m ON m.model = l.model
                LEFT JOIN (SELECT pajak_gabungan_id, count(id) AS total FROM tw_faktur_pajak_gabungan_line GROUP BY pajak_gabungan_id) pajak ON pajak.pajak_gabungan_id = fpg.id
                LEFT JOIN (
                    SELECT
                        fpg.id AS fpg_id,
                        SUM(amount_total) AS sum_total_amount,
                        SUM(untaxed_amount) AS sum_untaxed_amount,
                        SUM(tax_amount) AS sum_taxed_amount
                    FROM tw_faktur_pajak_out fpo2
                    LEFT JOIN tw_faktur_pajak_gabungan fpg
                        ON fpg.faktur_pajak_out_id = fpo2.id
                    GROUP BY fpg.id
                ) t ON t.fpg_id = fpg.id
            WHERE fpg.name IS NOT NULL %s
            ORDER BY b.code, fpg.date
        """ % query_where

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        if not ress:
            raise Warning('Data tidak ada...')

        return ress
