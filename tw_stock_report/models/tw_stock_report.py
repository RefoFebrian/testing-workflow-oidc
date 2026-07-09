from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError as Warning

class StockReport(models.TransientModel):
    _name = "tw.stock.report"
    _description = "Stock Report"

    def _get_default_company(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False

    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options_list(['Unit', 'Sparepart', 'Extras', 'Umum']))
    is_locked_division = fields.Boolean(string="Lock Division", default=False)
    options_unit = fields.Selection([
        ('detail', 'Detail Per Engine'),
        ('type_warna', 'Per Type Warna'),
        ('location', 'Per Location'),
        ('EV', 'Electric Vehicle')
    ], string='Option', default='detail')
    options_sparepart = fields.Selection([
        ('stock', 'Stock'),
        ('stock_reserved', 'Stock Reserved'),
        ('EV', 'Electric Vehicle')
    ], string='Options', default='stock')
    categ_ev = fields.Selection([
        ('EV', 'Unit EV'),
        ('EVBT', 'Battery'),
        ('EVCH','Charger')
    ], string='Categ EV')
    location_status = fields.Selection([
        ('all', 'Stock,Transit & Not Ready For Sale'),
        ('internal','Stock'),
        ('transit','Transit Mutasi'),
        ('nrfs','Not Ready For Sale')
    ], string='Location Status', default='all')

    company_ids = fields.Many2many(comodel_name='res.company', relation='tw_stock_report_company_rel',
                                  column1='stock_id', column2='company_id', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)], store=True)
    product_ids = fields.Many2many('product.product', 'tw_stock_report_product_rel', 'stock_id', 'product_id', 'Product')
    location_ids = fields.Many2many('stock.location', 'tw_stock_report_location_rel', 'stock_id', 'location_id', string='Location', domain=[('usage','=','internal')])

    @api.onchange("division")
    def _onchange_domain_product(self):
        self.options_unit = False
        self.options_sparepart = False
        self.categ_ev = False
        self.location_status = False
        self.company_ids = False
        self.product_ids = False
        self.location_ids = False
        
        domain = [('id', '=', 0)]
        if self.division:
            categ_ids = self.env['product.category'].get_child_ids(self.division)
            if categ_ids:
                product_ids = self.env['product.product'].search([
                    ('type', '!=', 'view'),
                    ('categ_id', 'in', categ_ids)
                ])
                if product_ids:
                    domain = [('id', 'in', product_ids.ids)]
        return {'domain': {'product_ids': domain}}
    
    def action_export_report(self, return_fp=False):
        if self.division == 'Unit':
            return self._action_export_unit_report(return_fp)
        else:
            if self.options_sparepart == 'stock_reserved':
                return self._export_sparepart_reserved_report(return_fp)
            else:
                return self._action_export_stock_sparepart_report(return_fp)

    def _sql_tuple(self, ids):
        """Format a list of IDs into a valid SQL tuple string for IN clauses.

        Python's single-element tuple (8,) has a trailing comma which is
        invalid SQL syntax. This helper produces (8) instead.
        """
        if not ids:
            return '(NULL)'
        return '(%s)' % ', '.join(str(i) for i in ids)

    def _prepare_filter(self):
        filter = ""
        branch_ids = self.env.user._get_company_ids()
        if self.company_ids:
            filter += " AND company.id IN %s" % self._sql_tuple(self.company_ids.ids)
        else:
            filter += " AND company.id IN %s" % self._sql_tuple(branch_ids)

        if self.product_ids:
            filter += " AND pp.id IN %s" % self._sql_tuple(self.product_ids.ids)
        if self.location_ids:
            filter += " AND location.id IN %s" % self._sql_tuple(self.location_ids.ids)
        if self.division:
            filter += " AND pp.division = '%s'" % (self.division,)

        if self.categ_ev:
            if self.categ_ev == 'EV':
                cond = "parent.name LIKE 'EV%%' AND parent.name NOT IN ('EVBT', 'EVCH')"
            else:
                cond = "parent.name = '%s'" % (self.categ_ev,)
            
            filter += """ AND cat.id IN (
                SELECT child.id
                FROM product_category child
                JOIN product_category parent ON child.parent_path LIKE (parent.parent_path || '%%')
                WHERE %s
            )""" % (cond,)
        
        if self.location_status:
            if self.location_status == 'all':
                filter += " AND location.usage IN ('internal', 'transit')"
            elif self.location_status == 'internal':
                filter += " AND location.usage = 'internal'"
            elif self.location_status == 'transit':
                filter += " AND location.usage = 'transit'"
            elif self.location_status == 'nrfs':
                filter += " AND location.usage = 'nrfs'"

        return filter

    def _action_export_stock_sparepart_report(self, return_fp=False):
        query = f"""
            WITH unconsolidated AS (
                -- Qty yang belum di-consolidate: incoming done moves dari PO yang consolidated_qty < quantity
                SELECT
                    sm.product_id,
                    sm.location_dest_id AS location_id,
                    sp.company_id,
                    SUM(sm.quantity - sm.consolidated_qty) AS qty_titipan
                FROM stock_move sm
                JOIN stock_picking sp ON sm.picking_id = sp.id
                JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                WHERE sm.state = 'assigned'
                  AND spt.code = 'incoming'
                  AND sm.consolidated_qty < sm.quantity
                GROUP BY sm.product_id, sm.location_dest_id, sp.company_id
            ),
            ranking AS (
                SELECT 
                    sub.company_id,
                    sub.product_id,
                    COUNT(DISTINCT sub.month_num) AS months_active -- Hitung bulan aktif sales
                FROM (
                    -- 1. Work Order
                    SELECT 
                        wo.company_id,
                        wol.product_id,
                        EXTRACT(MONTH FROM (wo.date + interval '7 hours'))::int AS month_num
                    FROM tw_work_order wo
                    JOIN tw_work_order_line wol ON wo.id = wol.order_id
                    JOIN product_product pp ON wol.product_id = pp.id
                    JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    JOIN product_category pc ON pt.categ_id = pc.id
                    WHERE wo.state = 'done'
                    AND wo.date >= date_trunc('month', CURRENT_DATE - INTERVAL '12 months')
                    AND wo.date < date_trunc('month', CURRENT_DATE)
                    AND pc.name != 'Service'
                    UNION ALL
                    -- 2. Part Sales
                    SELECT
                        ps.company_id,
                        psl.product_id,
                        EXTRACT(MONTH FROM (ps.create_date + interval '7 hours'))::int AS month_num
                    FROM tw_part_sales ps
                    JOIN tw_part_sales_line psl ON ps.id = psl.order_id
                    WHERE ps.state = 'done'
                    AND ps.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '12 months')
                    AND ps.create_date < date_trunc('month', CURRENT_DATE)
                ) sub
                GROUP BY sub.company_id, sub.product_id
            ),
            last_move AS (
                SELECT
                    sm.company_id,
                    sm.location_id,
                    sm.product_id,
                    MAX(sm.date) as last_date
                FROM stock_move sm
                JOIN stock_location sl ON sm.location_id = sl.id
                WHERE sm.state = 'done'
                AND sl.usage = 'internal'
                GROUP BY sm.company_id, sm.location_id, sm.product_id
            ),
            rfa_data AS (
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
                        wh.lot_stock_id as location_id, -- Asumsi SO mengambil stock dari Main Stock Warehouse
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
                -- Aging Stock (Formatted)
                , (TRUNC(AVG(DATE_PART('days', NOW() - quant.in_date)))::INTEGER || ' days') AS aging
                , location.complete_name AS lokasi
                -- Movement Aging (Formatted)
                , CASE WHEN lm.last_date IS NOT NULL 
                    THEN (TRUNC(DATE_PART('days', NOW() - lm.last_date))::INTEGER || ' days')
                    ELSE '-'
                END AS movement_aging
                -- qty_titipan: dari CTE unconsolidated (capped oleh total stock on hand)
                , LEAST(SUM(quant.quantity), COALESCE(MAX(uc.qty_titipan), 0)) AS qty_titipan
                , ROUND(
                    (LEAST(SUM(quant.quantity), COALESCE(MAX(uc.qty_titipan), 0))
                    * COALESCE(CAST(pp.standard_price ->> CAST(company.id AS TEXT) AS FLOAT), 0.00))::NUMERIC, 
                    2
                ) AS amount_titipan
                -- Qty RFA (MO/SO)
                , COALESCE(rfa.qty_rfa, 0) AS qty_rfa
                , ROUND(
                    (COALESCE(rfa.qty_rfa, 0) * COALESCE(CAST(pp.standard_price ->> CAST(company.id AS TEXT) AS FLOAT), 0.00))::NUMERIC, 
                    2
                ) AS amount_rfa
                , SUM(quant.reserved_quantity) AS qty_reserved
                , ROUND(
                    (SUM(quant.reserved_quantity) 
                    * COALESCE(CAST(pp.standard_price ->> CAST(company.id AS TEXT) AS FLOAT), 0.00))::NUMERIC, 
                    2
                ) AS amount_reserved
                , ROUND(
                    COALESCE(CAST(pp.standard_price ->> CAST(company.id AS TEXT) AS FLOAT), 0.00)::NUMERIC, 
                    2
                ) AS harga_satuan
                -- qty_available: total stock dikurangi titipan dan reserved
                , GREATEST(
                    SUM(quant.quantity)
                    - LEAST(SUM(quant.quantity), COALESCE(MAX(uc.qty_titipan), 0))
                    - SUM(quant.reserved_quantity),
                    0
                ) AS qty_available
                , ROUND(
                    (GREATEST(
                        SUM(quant.quantity)
                        - LEAST(SUM(quant.quantity), COALESCE(MAX(uc.qty_titipan), 0))
                        - SUM(quant.reserved_quantity),
                        0
                    ) * COALESCE(CAST(pp.standard_price ->> CAST(company.id AS TEXT) AS FLOAT), 0.00))::NUMERIC, 
                    2
                ) AS amount_available
                -- Total Stock = semua quant on hand
                , SUM(quant.quantity) AS "Total Stock (Qty)" 
                , ROUND(
                    (SUM(quant.quantity) * COALESCE(CAST(pp.standard_price ->> CAST(company.id AS TEXT) AS FLOAT), 0.00))::NUMERIC, 
                    2
                ) AS "Total Stock (Amt)"
                , CASE
                    WHEN COALESCE(MAX(rk.months_active), 0) >= 12 THEN 'A'
                    WHEN COALESCE(MAX(rk.months_active), 0) >= 9 THEN 'B'
                    WHEN COALESCE(MAX(rk.months_active), 0) >= 5 THEN 'C'
                    WHEN COALESCE(MAX(rk.months_active), 0) >= 1 THEN 'D'
                    ELSE 'E'
                END AS ranking_part
            FROM stock_quant quant
            LEFT JOIN res_company company ON quant.company_id = company.id
            JOIN stock_location location ON quant.location_id = location.id
            JOIN product_product pp ON quant.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN tw_selection ts ON location.type_id = ts.id
            LEFT JOIN product_category cat ON pt.categ_id = cat.id
            LEFT JOIN ranking rk ON rk.product_id = pp.id AND rk.company_id = company.id
            LEFT JOIN last_move lm ON lm.product_id = pp.id AND lm.location_id = location.id AND lm.company_id = company.id
            LEFT JOIN rfa_data rfa ON rfa.product_id = pp.id AND rfa.location_id = location.id AND rfa.company_id = company.id
            LEFT JOIN unconsolidated uc ON uc.product_id = pp.id AND uc.location_id = location.id AND uc.company_id = company.id
            WHERE location.usage IN ('internal', 'transit')
            AND pp.division = '{self.division}'
            AND quant.quantity > 0
            AND quant.quantity > COALESCE(quant.reserved_quantity,0)
            {self._prepare_filter()}
            GROUP BY company.id, cat.name, pp.id, pt.name, location.id, ts.name, lm.last_date, rfa.qty_rfa
            ORDER BY company.code, pp.default_code, location.complete_name
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()

        return self.env['web.report'].sudo().generate_report(
            f'Report Stock {self.division.title()}',
            result,
            return_fp=return_fp,
        )
    
    def _export_sparepart_reserved_report(self, return_fp=False):
        """Report untuk stock yang sedang dalam proses reserved (ada di picking)."""
        query = f"""
            SELECT 
                company.code AS branch_code
                , company.name AS branch_name
                , company.profit_centre AS branch_profit_center
                , cat.name AS kategori
                , pp.default_code AS kode_product
                , pt.name->>'en_US' AS nama_product
                , location.complete_name AS nama_lokasi
                , (DATE_PART('days', NOW() - quant.in_date)::INTEGER || ' days') AS aging
                , quant.quantity AS quantity
                , ROUND(COALESCE(CAST(pp.standard_price ->> CAST(company.id AS TEXT) AS FLOAT), 0.00)::NUMERIC, 2) AS harga_satuan
                , ROUND((quant.quantity * COALESCE(CAST(pp.standard_price ->> CAST(company.id AS TEXT) AS FLOAT), 0.00))::NUMERIC, 2) AS total_harga
                , 'Stock (Reserved)' AS status
                , sm.origin AS transaction_name
                , sp.name AS picking_name
            FROM stock_quant quant
            JOIN res_company company ON quant.company_id = company.id
            JOIN stock_location location ON quant.location_id = location.id
            JOIN product_product pp ON quant.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN tw_selection ts ON location.type_id = ts.id
            LEFT JOIN product_category cat ON pt.categ_id = cat.id
            -- Join untuk mendapatkan info reserved moves
            JOIN tw_stock_quant_stock_move_rel rel ON rel.quant_id = quant.id
            JOIN stock_move sm ON rel.move_id = sm.id
            LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
            WHERE location.usage IN ('internal', 'transit')
            {self._prepare_filter()}
            ORDER BY company.code, pp.default_code, location.complete_name
        """
        
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        
        return self.env['web.report'].sudo().generate_report(
            f'Report Stock Reserved {self.division.title()}',
            result,
            return_fp=return_fp,
        )

    def _action_export_unit_report(self, return_fp=False):
        """Router untuk Unit report berdasarkan options_unit."""
        if self.options_unit == 'location':
            return self._export_unit_location_report(return_fp)
        elif self.options_unit == 'type_warna':
            return self._export_unit_color_report(return_fp)
        else:
            # 'detail' atau 'EV'
            return self._export_unit_detail_report(return_fp)

    def _export_unit_detail_report(self, return_fp=False):
        """Report detail per engine number."""
        filter_clause = self._prepare_filter()
        
        query = f"""
            WITH last_picking AS (
                -- Ambil picking terakhir per lot
                SELECT DISTINCT ON (sml.lot_id)
                    sml.lot_id,
                    pick.date_done,
                    pick.name AS picking_name,
                    pick.origin,
                    pick.company_id
                FROM stock_move_line sml
                JOIN stock_picking pick ON sml.picking_id = pick.id
                WHERE sml.state = 'done'
                ORDER BY sml.lot_id, pick.date_done DESC
            )
            SELECT
                company.code AS branch_code,
                company.name AS branch_name,
                company.profit_centre AS profit_centre,
                pt.default_code AS product_type,
                pav.code ||'-'|| (pav.name->>'en_US') AS color,
                TO_CHAR((quant.in_date + INTERVAL '7 hours'), 'YYYY-MM-DD HH24:MI:SS') AS incoming_date,
                (DATE_PART('days', NOW() - (quant.in_date + INTERVAL '7 hours'))::INTEGER || ' days') AS stock_aging,
                location.complete_name AS location,
                (DATE_PART('days', NOW() - COALESCE(lp.date_done, quant.in_date) + INTERVAL '7 hours')::INTEGER || ' days') AS movement_aging,
                lot.name AS engine_number,
                lot.chassis_number AS chassis_number,
                CASE
                    WHEN location.usage = 'transit' THEN 'Intransit Mutasi'
                    WHEN lot.state = 'intransit' THEN 'Intransit Beli'
                    WHEN lot.state = 'stock' AND lot.ready_for_sale = 'not_good' THEN 'Stock NRFS'
                    WHEN lot.state = 'stock' THEN 'Stock RFS'
                    WHEN lot.state = 'reserved' THEN 'Stock Reserved'
                    WHEN lot.state = 'workshop' THEN 'Workshop'
                    WHEN lot.state ILIKE 'paid%%' OR lot.state ILIKE 'sold%%' THEN 'Undelivered'
                    ELSE lot.state
                END AS engine_state,
                lot.production_year AS year,
                quant.quantity AS qty,
                COALESCE(lot.cogs, 0) AS cost,
                lot.freight_cost AS freight_cost,
                lp.picking_name AS last_movement,
                CASE
                    WHEN lot.state ILIKE 'paid%%' OR lot.state ILIKE 'sold%%' THEN dso.name
                    WHEN lot.state = 'reserved' THEN dsor.name
                    WHEN lot.state = 'intransit' THEN po.name
                    WHEN location.usage = 'transit' THEN mo.name
                    ELSE lp.origin
                END AS last_transaction,
                COALESCE(rp.name, '') AS branch_destination,
                parent_categ.name AS parent_category,
                cat.name AS category_name,
                pt.name->>'en_US' AS series,
                lot.receive_date AS incoming_date_mutation
            FROM stock_quant quant
            INNER JOIN stock_lot lot ON quant.lot_id = lot.id
            JOIN product_product pp ON quant.product_id = pp.id
            JOIN stock_location location ON quant.location_id = location.id
            LEFT JOIN res_company company ON quant.company_id = company.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN product_category cat ON pt.categ_id = cat.id
            LEFT JOIN product_category parent_categ ON cat.parent_id = parent_categ.id
            LEFT JOIN product_category root_categ ON cat.root_category_id = root_categ.id
            LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = pp.id
            LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            LEFT JOIN tw_dealer_sale_order_line dsol ON lot.id = dsol.lot_id
            LEFT JOIN tw_dealer_sale_order_line dsolr ON lot.id = dsolr.lot_id AND lot.state = 'reserved'
            LEFT JOIN tw_dealer_sale_order dso ON dsol.order_id = dso.id
            LEFT JOIN tw_dealer_sale_order dsor ON dsolr.order_id = dsor.id
            LEFT JOIN purchase_order po ON po.id = lot.purchase_order_id
            LEFT JOIN last_picking lp ON lp.lot_id = lot.id
            LEFT JOIN tw_mutation_order mo ON lp.origin = mo.name AND lp.company_id = mo.company_id
            LEFT JOIN res_partner rp ON mo.requester_id = rp.id
            WHERE location.usage IN ('internal', 'transit')
            AND quant.quantity>0
            {filter_clause}

            UNION ALL

            -- Intransit AHM (MD only)
            SELECT
                company.code AS branch_code,
                company.name AS branch_name,
                company.profit_centre AS profit_centre,
                pt.default_code AS product_type,
                pav.code ||'-'|| (pav.name->>'en_US') AS color,
                TO_CHAR((lot.create_date + INTERVAL '7 hours'), 'YYYY-MM-DD HH24:MI:SS') AS incoming_date,
                (DATE_PART('days', NOW() - (lot.create_date + INTERVAL '7 hours'))::INTEGER || ' days') AS stock_aging,
                location.complete_name AS location,
                (DATE_PART('days', NOW() - (lot.create_date + INTERVAL '7 hours'))::INTEGER || ' days') AS movement_aging,
                lot.name AS engine_no,
                lot.chassis_number AS chassis_no,
                'Intransit AHM' AS engine_state,
                lot.production_year AS year,
                1 AS qty,
                COALESCE(lot.cogs, 0) AS cost,
                lot.freight_cost AS freight_cost,
                lot.ship_list_number AS last_movement,
                po.name AS last_transaction,
                '' AS branch_destination,
                root_categ.name AS cat2_name,
                cat.name AS cat_name,
                pt.name->>'en_US' AS series,
                lot.receive_date AS in_date_mutation
            FROM stock_lot lot
            JOIN product_product pp ON lot.product_id = pp.id
            LEFT JOIN res_company company ON lot.company_id = company.id
            LEFT JOIN tw_selection ts ON company.branch_type_id = ts.id
            LEFT JOIN stock_location location ON lot.location_id = location.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN product_category cat ON pt.categ_id = cat.id
            LEFT JOIN product_category root_categ ON cat.root_category_id = root_categ.id
            LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = pp.id
            LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            LEFT JOIN purchase_order po ON po.id = lot.purchase_order_id
            WHERE lot.state = 'intransit'
            AND ts.value = 'MD'
            AND pt.is_storable = True
            {filter_clause}
            ORDER BY branch_code, engine_state, location, product_type, color
        """
        
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        
        title = 'Report Stock Unit EV' if self.options_unit == 'EV' else 'Report Stock Unit'
        return self.env['web.report'].sudo().generate_report(
            title, result, return_fp=return_fp
        )

    def _export_unit_location_report(self, return_fp=False):
        """Report summary per lokasi (capacity vs total stock)."""
        filter_clause = self._prepare_filter()
        
        query = f"""
            SELECT
                company.code AS branch_code,
                company.name AS branch_name,
                location.complete_name AS location_name,
                ts.value AS type_location,
                location.effective_start_date AS start_date,
                location.effective_end_date AS end_date,
                COALESCE(location.capacity, 0) AS capacity,
                COALESCE(SUM(quant.quantity), 0) AS total_stock,
                COALESCE(location.capacity, 0) - COALESCE(SUM(quant.quantity), 0) AS available_capacity
            FROM stock_location location
            LEFT JOIN stock_quant quant ON quant.location_id = location.id
            LEFT JOIN res_company company ON location.company_id = company.id
            LEFT JOIN tw_selection ts ON location.type_id = ts.id
            LEFT JOIN product_product pp ON quant.product_id = pp.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN product_category cat ON pt.categ_id = cat.id
            LEFT JOIN product_category root_categ ON cat.root_category_id = root_categ.id
            WHERE location.usage = 'internal'
            {filter_clause}
            GROUP BY company.id, location.id, ts.id
            ORDER BY company.code, location.complete_name
        """
        
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        
        return self.env['web.report'].sudo().generate_report(
            'Report Stock Unit Per Location', result, return_fp=return_fp
        )

    def _export_unit_color_report(self, return_fp=False):
        """Report summary per type dan warna."""
        filter_clause = self._prepare_filter()
        
        query = f"""
            SELECT
                company.code AS branch_code,
                company.name AS branch_name,
                pt.default_code AS product_code,
                pt.name->>'en_US' AS product_name,
                pav.code AS color_code,
                pav.name->>'en_US' AS color_name,
                SUM(quant.quantity) AS total_quantity
            FROM stock_quant quant
            JOIN stock_location location ON location.id = quant.location_id
            JOIN res_company company ON company.id = quant.company_id
            JOIN stock_lot lot ON lot.id = quant.lot_id
            JOIN product_product pp ON pp.id = quant.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = pp.id
            LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            LEFT JOIN product_category cat ON cat.id = pt.categ_id
            LEFT JOIN product_category root_categ ON cat.root_category_id = root_categ.id
            WHERE location.usage = 'internal'
            AND lot.ready_for_sale = 'good'
            {filter_clause}
            GROUP BY company.id, pt.id, pav.id
            ORDER BY company.code, pt.default_code, pav.code
        """
        
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        
        return self.env['web.report'].sudo().generate_report(
            'Report Stock Unit Per Type Warna', result, return_fp=return_fp
        )
