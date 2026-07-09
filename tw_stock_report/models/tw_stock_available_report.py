from odoo import models, fields, api

class StockAvailableReport(models.TransientModel):
    _name = "tw.stock.available.report"
    _inherit = "tw.stock.report"
    _description = "Stock Available Report"

    company_ids = fields.Many2many(
        comodel_name='res.company', 
        relation='tw_stock_available_report_company_rel',
        column1='stock_id', 
        column2='company_id', 
        domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)], 
        store=True
    )
    product_ids = fields.Many2many(
        'product.product', 
        'tw_stock_available_report_product_rel', 
        'stock_id', 
        'product_id', 
        'Product'
    )
    location_ids = fields.Many2many(
        'stock.location', 
        'tw_stock_available_report_location_rel', 
        'stock_id', 
        'location_id', 
        string='Location', 
        domain=[('usage','=','internal')]
    )

    def action_export_report(self, return_fp=False):
        filter_clause = self._prepare_filter()
        
        query = f"""
            WITH rfa_data AS (
                SELECT
                    company_id,
                    location_id,
                    product_id,
                    SUM(qty) as qty_rfa
                FROM (
                    -- MO Data (RFA/Approved)
                    SELECT
                        mo.company_id,
                        mo.location_id,
                        mol.product_id,
                        mol.qty
                    FROM tw_mutation_order mo
                    JOIN tw_mutation_order_line mol ON mo.id = mol.mutation_order_id
                    WHERE mo.state IN ('rfa', 'approved') 
                    UNION ALL
                    -- SO Data (RFA/Approved)
                    SELECT 
                        so.company_id,
                        wh.lot_stock_id as location_id,
                        sol.product_id,
                        sol.product_uom_qty as qty
                    FROM sale_order so
                    JOIN sale_order_line sol ON so.id = sol.order_id
                    JOIN stock_warehouse wh ON so.warehouse_id = wh.id
                    WHERE so.state IN ('rfa', 'approved')
                ) rfa_sub
                GROUP BY company_id, location_id, product_id
            )
            SELECT 
                company.code AS branch_code
                , company.name AS branch_name
                , company.profit_centre AS profit_centre
                , cat.name AS kategori
                , pp.default_code AS kode_product
                , pt.name->>'en_US' AS nama_barang
                , location.complete_name AS lokasi
                , quant.quantity AS "Total Stock (Qty)"
                , COALESCE(rfa.qty_rfa, 0) AS qty_rfa
                , quant.reserved_quantity AS qty_reserved
                , quant.quantity - COALESCE(quant.reserved_quantity) - COALESCE(rfa.qty_rfa,0) AS available_qty
                , ROUND(
                    COALESCE(CAST(pp.standard_price ->> CAST(company.id AS TEXT) AS FLOAT), 0.00)::NUMERIC, 
                    2
                ) AS harga_satuan
            FROM stock_quant quant
            JOIN res_company company ON quant.company_id = company.id
            JOIN stock_location location ON quant.location_id = location.id
            JOIN product_product pp ON quant.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN tw_selection ts ON location.type_id = ts.id
            LEFT JOIN product_category cat ON pt.categ_id = cat.id
            LEFT JOIN rfa_data rfa ON rfa.product_id = pp.id AND rfa.location_id = location.id AND rfa.company_id = company.id
            WHERE location.usage IN ('internal', 'transit')
            AND quant.quantity > 0
            {filter_clause}
            ORDER BY company.code, pp.default_code, location.complete_name
        """
        
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        
        return self.env['web.report'].sudo().generate_report(
            'Report Stock Available',
            result,
            return_fp=return_fp,
        )
