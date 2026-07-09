# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class TWReportControlDF(models.TransientModel):
    _name = "tw.report.control.df"
    _description = "TW Report Control DF"

    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    per_date = fields.Date(string="Per Date", required=True)



    def action_generate_report(self):
        branch = self.env.user._get_company_ids()
        query = """
            SELECT 
                so.name as no_transaksi 
                , partner.code as code_cabang 
                , partner.name as nama_dealer 
                , ai.name as no_invoice 
                , TO_CHAR(ai.date, 'DD/MM/YYYY') AS tanggal_invoice
                , TO_CHAR(ai.invoice_date_due, 'DD/MM/YYYY') AS tanggal_jtp
                , ai.amount_total
                , inv_qty.quantity as qty_invoice 
                , coalesce(sj_qty.quantity,0) as qty_surat_jalan
                , TO_CHAR(sj_qty.date_done + interval '7 hours', 'DD/MM/YYYY') AS tanggal_picking
            FROM tw_sale_order so
                INNER JOIN (
                    SELECT so.id AS so_id
                        , inv.id AS inv_id
                        , SUM(invl.quantity) AS quantity
                    FROM tw_sale_order so
                    INNER JOIN account_move inv 
                        ON so.name = inv.ref
                    AND inv.move_type = 'out_invoice'
                    INNER JOIN account_move_line invl 
                        ON invl.move_id = inv.id
                        and invl.display_type = 'product'
                    WHERE so.division = 'Unit'
                    AND inv.date <= '%s'
                    GROUP BY so.id, inv.id
                ) inv_qty ON so.id = inv_qty.so_id
                LEFT JOIN (
                    SELECT so.id
                        , so.name
                        , string_agg(pick.name, ', ') as no_surat_jalan
                        , max(pick.date_done) as date_done
                        , SUM(sol.qty_delivered) as quantity 
                    FROM tw_sale_order so 
                    INNER JOIN tw_sale_order_line sol on sol.order_id = so.id 
                    INNER JOIN stock_picking pick on so.name = pick.origin and pick.state = 'done' 
                    INNER JOIN stock_picking_type spt on spt.id = pick.picking_type_id
                    INNER JOIN stock_move move ON move.picking_id = pick.id  and move.product_id = sol.product_id
                    INNER JOIN (
                        SELECT
                            move_id
                        FROM stock_move_line
                        WHERE lot_id IS NOT NULL
                        GROUP BY move_id
                    ) sml ON sml.move_id = move.id
                    WHERE so.division = 'Unit' 
                        AND spt.code ='outgoing'
                        AND pick.date_done <= to_timestamp('%s 23:59:59', 'YYYY-MM-DD HH24:MI:SS') + interval '7 hours' 
                    GROUP BY so.id, so.name
                ) sj_qty ON so.id = sj_qty.id --- sj_qty
                INNER JOIN account_move ai ON ai.id = inv_qty.inv_id AND ai.move_type = 'out_invoice' 
                LEFT JOIN res_company branch ON so.company_id = branch.id 
                LEFT JOIN res_partner partner ON so.partner_id = partner.id 
            WHERE 1=1
                AND (
                    inv_qty.quantity > sj_qty.quantity 
                    OR sj_qty.quantity is null 
                    OR (sj_qty.date_done >= to_timestamp('%s 00:00:00', 'YYYY-MM-DD HH24:MI:SS') + interval '7 hours'
                )
                AND sj_qty.date_done <= to_timestamp('%s 23:59:59', 'YYYY-MM-DD HH24:MI:SS') + interval '7 hours') 
                AND branch.id in %s
            ORDER BY branch.code, ai.date, partner.code, so.name, ai.name, sj_qty.date_done, sj_qty.no_surat_jalan
        """ % (self.per_date, self.per_date, self.per_date, self.per_date, str(tuple(branch)).replace(',)', ')'))

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        if not ress:
            raise Warning('Data tidak ada...')
        report_name = f"Laporan Control DF"
        return self.env['web.report'].sudo().generate_report(report_name, ress, header_title=False, auto_filter=False, bottom_remark=False, show_total_footer=False, data_summary_header=False, data_summary_header_col_size=False, freeze_panes_column=3, remove_all_styling=True)