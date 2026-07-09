from odoo import api, fields, models
from datetime import datetime


class AssetReport(models.TransientModel):
    _name = "tw.asset.report"
    _description = "Asset Report"

    option = fields.Selection([
        ('prepaid','Prepaid'), 
        ('asset','Asset')], 
        'Option', 
        required=True, 
        default='asset')
    status = fields.Selection([
        ('all','All'), 
        ('active','Active'), 
        ('disposed','Disposed'), 
        ('draft','Draft')], 
        'Status', 
        required=True, 
        default='all')

    company_ids = fields.Many2many('res.company', 'tw_asset_report_company_rel', 'report_id', 'company_id', string="Branch")
    category_ids = fields.Many2many('account.asset.category', 'tw_asset_report_category_rel', 'report_id', 'category_id', string='Category')

    def action_export_report(self,return_fp=False):
        query_where = "WHERE 1=1 "
        if self.option == 'prepaid':
            query_where += " AND asset.type_assets = 'asset_prepayments'"
        
        if self.status != 'all':
            query_where += f" AND asset.state = '{str(self.status)}'"

        if self.company_ids:
            query_where += f" AND asset.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND asset.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.category_ids:
            category_ids = str(tuple([b.id for b in self.category_ids])).replace(',)', ')')
            query_where += f" AND asset.category_id in {category_ids}"

        query = f"""
           SELECT 
                asset.division AS division, 
                branch.code AS branch_code, 
                asset.code AS asset_code, 
                asset.name AS asset_name, 
                category.asset_code AS category_code, 
                asset.method_number AS asset_method_number, 
                account_asset.name->>'en_US' AS account_asset_code,  
                account_expense.name->>'en_US' AS account_expense_code, 
                asset.purchase_date AS asset_purchase_date, 
                COALESCE(asset.real_purchase_value,0) AS asset_real_purchase_value, 
                CASE 
                    WHEN COALESCE(asset.method_number,0) = 0 THEN 0
                    ELSE (COALESCE(asset.value,0) - COALESCE(asset.salvage_value,0)) / COALESCE(asset.method_number,0) 
                END AS susut_perbulan,
                COALESCE(depreline.cnt,0) AS jumlah_susut, 
                COALESCE(asset.real_purchase_value,0) - COALESCE(asset.value,0) + COALESCE(susut.amount,0) AS total_depresiasi,
                COALESCE(asset.value,0) - COALESCE(susut.amount,0) - COALESCE(asset.salvage_value,0) AS residual_value,
                asset.state AS state
                , asset.name AS register
                , picking.name AS receive_name
                , rp.code AS vendor_code
                , rp.name AS vendor_name
                , disposal.name AS disposal_name
                , disposal.date AS disposal_date
                , coalesce(disposal.amount_subtotal,0) AS disposal_price
                , coalesce(disposal.tax,0) AS disposal_tax
                , rp2.code AS disposal_vendor_code
                , rp2.name AS disposal_vendor_name
                , asset.purchase_date AS purchase_date
                , loc.name AS lokasi_aset
                , pma.name AS no_peminjaman
                , pmal.rent_date AS tgl_peminjaman
                , pma.start_date start_date
                , pma.end_date end_date
                , pengembalian.confirm_date tgl_pengembalian
                , resp.name AS responsible_name
                , asset.note AS note
            FROM account_asset_asset asset
            left join res_company branch on branch.id = asset.company_id
            left join tw_good_receive_assets gr_assets on asset.id = gr_assets.asset_register_id
            LEFT JOIN stock_picking picking ON picking.id = gr_assets.picking_id
            LEFT JOIN tw_good_receive_asset_line tgral ON tgral.picking_id = picking.id
            LEFT JOIN product_product pp ON pp.id = asset.product_id
            left join product_template pt on pt.id = pp.product_tmpl_id
            LEFT JOIN res_partner rp ON rp.id = asset.partner_id
            LEFT JOIN (
                SELECT amount, asset_id, cnt
                FROM account_asset_depreciation_line
                INNER JOIN (
                    SELECT MAX(id) AS max_id, COUNT(id) AS cnt
                    FROM account_asset_depreciation_line
                    WHERE move_check = true
                    GROUP BY asset_id
                ) AS max_line ON id = max_line.max_id
            ) AS depreline ON depreline.asset_id = asset.id
            LEFT JOIN (
                SELECT 
                    aadl.asset_id AS asset_id, 
                    SUM(abs(l.debit-l.credit)) AS amount
                FROM account_move_line l
                join account_move mv on mv.id = l.move_id
                join account_asset_depreciation_line aadl on aadl.move_id = mv.id
                GROUP BY aadl.asset_id
            ) AS susut ON susut.asset_id = asset.id
           LEFT JOIN (
            	SELECT 
                    tadl.asset_id,
                    da.name,
                    da.date,
                    da.partner_id,
                    tadl.amount_subtotal,
                    (tadl.amount-tadl.amount_subtotal) AS tax
                FROM tw_asset_disposal da 
                INNER JOIN tw_asset_disposal_line tadl ON da.id = tadl.disposal_id 
                WHERE da.state = 'confirm'
            ) AS disposal ON asset.id = disposal.asset_id 
            LEFT JOIN res_partner rp2 ON rp2.id = disposal.partner_id
            LEFT JOIN account_asset_category category ON category.id = asset.category_id 
            LEFT JOIN account_account account_asset ON account_asset.id = category.account_asset_id 
            LEFT JOIN account_account account_expense ON account_expense.id = category.account_depreciation_expense_id
            LEFT JOIN stock_location loc ON asset.location_id = loc.id
            LEFT JOIN tw_asset_lending pma ON asset.rent_id = pma.id
            LEFT JOIN tw_asset_lending_line pmal ON pma.id = pmal.rent_id AND asset.id = pmal.asset_id
            LEFT JOIN tw_asset_return_line pengembalian_line ON pma.id = pengembalian_line.rent_id AND asset.id = pengembalian_line.asset_id
            LEFT JOIN tw_asset_return pengembalian ON pengembalian_line.return_id = pengembalian.id
            LEFT JOIN hr_employee resp ON resp.id = asset.employee_id
            {query_where}
        """.format(query_where=query_where)
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Report Assets', result, return_fp=return_fp)