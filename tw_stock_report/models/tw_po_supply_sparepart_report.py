from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning

class TWPoSupplySparepartReport(models.TransientModel):
    _name = "tw.po.supply.sparepart.report"
    _description = "PO Supply Sparepart Report"

    def _get_default_date(self):
        return datetime.now()

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)

    partner_ids = fields.Many2many('res.partner', 'tw_report_po_supply_sparepart_partner_rel', 'tw_report_po_supply_sparepart_id', 'partner_id', string='Branches', domain=[('category_id.name', 'in', ['Branch', 'Dealer'])])

    def action_export_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = ""
        if self.start_date:
            query_where += f" AND sd.date >= '{self.start_date}'"

        if self.end_date:
            query_where += f" AND sd.date <= '{self.end_date}'"

        if self.partner_ids:
            query_where += f" AND sd.requester_id IN {str(tuple(self.partner_ids.ids)).replace(',)', ')')}"

        query = f"""
            SELECT
                COALESCE(po.default_code, '') "Product Code",
                COALESCE(po.name_template, '') "Product Description",
                COALESCE(po.qty_additional, 0) "Qty PO Additional",
                COALESCE(po.qty_fix, 0) "Qty PO Fix",
                COALESCE(po.qty_hotline, 0) "Qty PO Hotline",
                COALESCE(po.qty_simpart, 0) "Qty PO Simpart",
                COALESCE(po.qty_topup, 0) "Qty PO Topup",
                COALESCE(po.supply, 0) "Qty Supply",
                COALESCE(po.back_order, 0) "Qty Back Order",
                CASE WHEN stock.location_type NOT IN ('topup', 'backup_hotline', 'hotline')
                    THEN stock.qty - (stock.qty_reserved + stock.qty_rfa_approved) ELSE 0 END "Stock Available",
                CASE WHEN stock.location_type = 'topup'
                    THEN stock.qty - (stock.qty_reserved + stock.qty_rfa_approved) ELSE 0 END "Stock Available Topup",
                CASE WHEN stock.location_type = 'backup_hotline'
                    THEN stock.qty - (stock.qty_reserved + stock.qty_rfa_approved) ELSE 0 END "Stock Available Backup Hotline",
                CASE WHEN stock.location_type = 'hotline'
                    THEN stock.qty - (stock.qty_reserved + stock.qty_rfa_approved) ELSE 0 END "Stock Available Hotline"
            FROM (
                SELECT
                    p.id AS product_id,
                    t.name ->> 'en_US' AS name_template,
                    p.default_code,
                    SUM(CASE WHEN pot.name = 'Additional' THEN sdl.approved_qty ELSE 0 END) AS qty_additional,
                    SUM(CASE WHEN pot.name = 'Fix' THEN sdl.approved_qty ELSE 0 END) AS qty_fix,
                    SUM(CASE WHEN pot.name = 'Hotline' THEN sdl.approved_qty ELSE 0 END) AS qty_hotline,
                    SUM(CASE WHEN pot.name = 'Simpart' THEN sdl.approved_qty ELSE 0 END) AS qty_simpart,
                    SUM(CASE WHEN pot.name = 'Topup' THEN sdl.approved_qty ELSE 0 END) AS qty_topup,
                    SUM(sdl.supply_qty) AS supply,
                    SUM(sdl.approved_qty - sdl.supply_qty) AS back_order
                FROM tw_stock_distribution sd
                INNER JOIN res_company company ON company.id = sd.company_id AND company.code = 'MML'
                LEFT JOIN tw_stock_distribution_line sdl ON sdl.stock_distribution_id = sd.id
                LEFT JOIN tw_purchase_order_type pot ON sd.purchase_order_type_id = pot.id
                LEFT JOIN product_product p ON p.id = sdl.product_id
                LEFT JOIN product_template t ON t.id = p.product_tmpl_id
                WHERE 1=1
                    AND sd.division = 'Sparepart'
                    AND sd.state IN ('open', 'done')
                    {query_where}
                GROUP BY p.id, t.id
            ) AS po
            LEFT JOIN (
                SELECT
                    quant.product_id,
                    quant.location_type,
                    quant.qty,
                    COALESCE(reserved.qty_reserved, 0) AS qty_reserved,
                    COALESCE(so_rfa_approved.qty, 0) + COALESCE(mo_rfa_approved.qty, 0) AS qty_rfa_approved
                FROM (
                    SELECT
                        l.company_id,
                        l.usage AS location_usage,
                        loc_type.value AS location_type,
                        q.product_id,
                        SUM(q.quantity) AS qty,
                        q.location_id
                    FROM stock_quant q
                    INNER JOIN stock_location l ON q.location_id = l.id
                    INNER JOIN tw_selection loc_type ON loc_type.id = l.type_id
                    INNER JOIN product_product p ON q.product_id = p.id
                    INNER JOIN product_template t ON p.product_tmpl_id = t.id
                    INNER JOIN res_company c ON l.company_id = c.id AND c.code = 'MML'
                    WHERE t.division = 'Sparepart'
                        AND loc_type.value IN ('rfs', 'topup', 'hotline', 'backup_hotline')
                    GROUP BY l.company_id, l.usage, loc_type.value, q.product_id, q.location_id
                ) AS quant
                LEFT JOIN (
                    SELECT
                        sm.product_id,
                        sm.location_id,
                        sp.company_id,
                        SUM(sm.product_uom_qty) AS qty_reserved
                    FROM stock_move sm
                    INNER JOIN stock_picking sp ON sm.picking_id = sp.id
                    INNER JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                    INNER JOIN res_company c ON sp.company_id = c.id AND c.code = 'MML'
                    WHERE spt.code IN ('outgoing', 'internal')
                        AND sp.state NOT IN ('draft', 'cancel', 'done')
                        AND sp.division = 'Sparepart'
                    GROUP BY sm.product_id, sm.location_id, sp.company_id
                ) AS reserved ON quant.product_id = reserved.product_id
                    AND quant.location_id = reserved.location_id
                    AND quant.company_id = reserved.company_id
                    AND quant.location_usage = 'internal'
                LEFT JOIN (
                    SELECT
                        so.company_id,
                        sol.product_id,
                        so.location_id,
                        SUM(sol.product_uom_qty) AS qty
                    FROM tw_sale_order_line sol
                    INNER JOIN tw_sale_order so ON sol.order_id = so.id
                    WHERE so.division = 'Sparepart'
                        AND so.state IN ('waiting_for_approval', 'approved')
                    GROUP BY so.company_id, sol.product_id, so.location_id
                ) AS so_rfa_approved ON quant.company_id = so_rfa_approved.company_id
                    AND quant.product_id = so_rfa_approved.product_id
                    AND quant.location_id = so_rfa_approved.location_id
                LEFT JOIN (
                    SELECT
                        mo.company_id,
                        mol.product_id,
                        mo.location_id,
                        SUM(mol.qty) AS qty
                    FROM tw_mutation_order_line mol
                    INNER JOIN tw_mutation_order mo ON mol.mutation_order_id = mo.id
                    WHERE mo.division = 'Sparepart'
                        AND mo.state IN ('waiting_for_approval', 'approved')
                    GROUP BY mo.company_id, mol.product_id, mo.location_id
                ) AS mo_rfa_approved ON quant.company_id = mo_rfa_approved.company_id
                    AND quant.product_id = mo_rfa_approved.product_id
                    AND quant.location_id = mo_rfa_approved.location_id
            ) AS stock ON stock.product_id = po.product_id
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report(
            'Report PO Supply Sparepart',
            result,
            start_date=self.start_date,
            end_date=self.end_date
        )

