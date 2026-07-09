from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError as Warning

class TWRankingSparepartReport(models.TransientModel):
    _name = "tw.ranking.sparepart.report"
    _description = "Laporan Ranking Sparepart"

    company_ids = fields.Many2many('res.company','tw_ranking_sparepart_report_company_rel','ranking_sparepart_id','company_id', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    categ_ids = fields.Many2many('product.category', 'tw_ranking_sparepart_report_categ_rel', 'ranking_sparepart_id','categ_id', 'Category', domain="[('parent_id', '!=', False)]")

    def action_export_report(self):
        query_where = ""
        if self.company_ids:
            query_where += f" AND company.id IN ({', '.join(str(company.id) for company in self.company_ids)})"
        else:
            companies = self.env.user._get_company_ids()
            query_where += f" AND company.id IN {str(tuple(companies)).replace(',)', ')')}"
            
        if self.categ_ids:
            query_where += f" AND pc.id IN ({', '.join(str(categ.id) for categ in self.categ_ids)})"

        query = f"""
            WITH base AS (
                (
                SELECT
                    company.code AS branch,
                    pt.name->>'en_US' AS kode_part,
                    product.default_code AS nama_part,
                    pc.name AS category,
                    EXTRACT(MONTH FROM (wo.date + interval '7 hours'))::int AS bulan,
                    1 AS qty
                FROM tw_work_order wo
                LEFT JOIN tw_work_order_line wol ON wo.id = wol.order_id
                LEFT JOIN product_product product ON product.id = wol.product_id
                LEFT JOIN product_template pt ON pt.id = product.product_tmpl_id
                LEFT JOIN res_company company ON company.id = wo.company_id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                WHERE 
                    wo.date BETWEEN date_trunc('month', current_date - interval '12 month') 
                    AND (date_trunc('month', current_date) - interval '1 day')
                    AND pc.name != 'Service'
                    AND wo.state = 'done'
                    {query_where}
                )
                UNION ALL
                (
                SELECT
                    company.code AS branch,
                    pt.name->>'en_US' AS kode_part,
                    product.default_code AS nama_part,
                    pc.name AS category,
                    EXTRACT(MONTH FROM (ps.create_date + interval '7 hours'))::int AS bulan,
                    1 AS qty
                FROM tw_part_sales ps
                LEFT JOIN tw_part_sales_line psl ON ps.id = psl.order_id
                LEFT JOIN product_product product ON product.id = psl.product_id
                LEFT JOIN product_template pt ON pt.id = product.product_tmpl_id
                LEFT JOIN res_company company ON company.id = ps.company_id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                WHERE 
                    ps.create_date BETWEEN date_trunc('month', current_date - interval '12 month') 
                    AND (date_trunc('month', current_date) - interval '1 day')
                    AND ps.state = 'done'
                    {query_where}
                )
            ),
            agg AS (
                SELECT
                    branch, kode_part, nama_part,
                    category, bulan,
                    COUNT(qty) AS total_per_bulan
                FROM base
                GROUP BY branch, kode_part, nama_part, category, bulan
            ),
            main_result AS (
                SELECT
                    branch,
                    kode_part,
                    nama_part,
                    category,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 1), 0)::float AS january,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 2), 0)::float AS february,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 3), 0)::float AS march,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 4), 0)::float AS april,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 5), 0)::float AS may,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 6), 0)::float AS june,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 7), 0)::float AS july,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 8), 0)::float AS august,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 9), 0)::float AS september,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 10), 0)::float AS october,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 11), 0)::float AS november,
                    COALESCE(SUM(total_per_bulan) FILTER (WHERE bulan = 12), 0)::float AS december,
                    SUM((total_per_bulan > 0)::int) AS total_penjualan_bulan_berjalan
                FROM agg
                GROUP BY branch, kode_part, nama_part, category
            )
            SELECT
                branch, kode_part, nama_part, category,
                january, february, march, april, may, june,
                july, august, september, october, november, december,
                (january + february + march + april + may + june +
                july + august + september + october + november + december) AS total_penjualan,
                total_penjualan_bulan_berjalan::float,
                CASE
                    WHEN total_penjualan_bulan_berjalan >= 12 THEN 'A'
                    WHEN total_penjualan_bulan_berjalan >= 9  THEN 'B'
                    WHEN total_penjualan_bulan_berjalan >= 5  THEN 'C'
                    WHEN total_penjualan_bulan_berjalan >= 1  THEN 'D'
                    ELSE 'E'
                END AS rank
            FROM main_result
            ORDER BY branch, kode_part, nama_part
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Laporan Ranking Sparepart', result, freeze_panes_column=5)