# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import pytz
import base64
import csv
import xlsxwriter
import calendar
from io import StringIO,BytesIO
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwWPPReport(models.TransientModel):
    _inherit = "tw.lbb.report"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods

    def _print_excel_report_prestasi_mekanik_detil(self):
        company_id = self.company_ids  
        start_date = self.start_date
        end_date = self.end_date
        
        if not company_id :
            query_company_id = " is not null "
        else:
            query_company_id = " in %s " % str(tuple(company_id)).replace(',)', ')')

        query_where =" '%s' and '%s' "%(start_date,end_date)
        query = f"""
            SELECT      
                branch.id
                ,branch.name
                ,COALESCE(wo.mechanic_id,0) as mechanic_id 
                ,COALESCE(rr.name,'Part Cash') as nama
                ,COUNT(DISTINCT (wo.lot_id::VARCHAR || (wo.open_date + interval '7 hours')::DATE::VARCHAR)) FILTER (WHERE type.value not in ('WAR','SLS')) AS cnt_unit
                ,SUM(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) * COALESCE(wol.product_uom_qty,0)) FILTER (WHERE wol.division = 'Service') amt_jasa 
                ,SUM(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) * wol.qty_delivered) FILTER (WHERE wol.division = 'Sparepart' AND pc.name = 'OIL') amt_oil 
                ,SUM(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) * wol.qty_delivered) FILTER (WHERE wol.division = 'Sparepart' AND pc.name NOT IN ( 'OLI','OIL')) amt_part 
                ,SUM(COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100) / (1 + COALESCE(tax.amount,0)) * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE COALESCE(wol.product_uom_qty,0) END) amt_total 
                ,SUM(COALESCE(wol.product_uom_qty,0)) FILTER (WHERE wol.division = 'Service' AND pc.name = 'CLA') qty_cla 
                ,SUM(COALESCE(wol.product_uom_qty,0)) FILTER (WHERE wol.division = 'Service' AND pc.name = 'CS') qty_cs 
                ,SUM(COALESCE(wol.product_uom_qty,0)) FILTER (WHERE wol.division = 'Service' AND pc.name = 'HR') qty_hr 
                ,SUM(COALESCE(wol.product_uom_qty,0)) FILTER (WHERE wol.division = 'Service' AND pc2.name = 'KPB') qty_kpb 
                ,SUM(COALESCE(wol.product_uom_qty,0)) FILTER (WHERE wol.division = 'Service' AND pc.name = 'LR') qty_lr 
                ,SUM(COALESCE(wol.product_uom_qty,0)) FILTER (WHERE wol.division = 'Service' AND pc.name = 'LS') qty_ls 
                ,SUM(COALESCE(wol.product_uom_qty,0)) FILTER (WHERE wol.division = 'Service' AND pc.name = 'OR+') qty_or 
                ,SUM(COALESCE(wol.product_uom_qty,0)) FILTER (WHERE wol.division = 'Service' AND pc2.name = 'QS') qty_qs 
                ,SUM(COALESCE(wol.product_uom_qty,0)) FILTER (WHERE wol.division = 'Service') qty_total

                -- KPB
                ,COUNT(DISTINCT wo.id) AS cnt_inv 
                ,COUNT(DISTINCT wo.id) FILTER (WHERE type.value = 'CLA') AS cnt_cla
                ,COUNT(DISTINCT wo.id) FILTER (WHERE type.value = 'KPB' AND wo.kpb_ke = '1') AS cnt_kpb_1 
                ,COUNT(DISTINCT wo.id) FILTER (WHERE type.value = 'KPB' AND wo.kpb_ke = '2') AS cnt_kpb_2 
                ,COUNT(DISTINCT wo.id) FILTER (WHERE type.value = 'KPB' AND wo.kpb_ke = '3') AS cnt_kpb_3 
                ,COUNT(DISTINCT wo.id) FILTER (WHERE type.value = 'KPB' AND wo.kpb_ke = '4') AS cnt_kpb_4 

            FROM tw_work_order wo
            INNER JOIN account_move ai
            ON wo.name = ai.invoice_origin
            INNER JOIN tw_work_order_line wol ON wo.id = wol.order_id
            LEFT JOIN tw_selection type on type.id = wo.type_id
            LEFT JOIN account_tax_tw_work_order_line_rel as wot on wot.tw_work_order_line_id = wol.id
            LEFT JOIN account_tax as tax on tax.id = wot.account_tax_id
            LEFT JOIN product_product p ON wol.product_id = p.id
            LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id
            LEFT JOIN product_category pc ON pt.categ_id = pc.id
            LEFT JOIN product_category pc2 ON pc.parent_id = pc2.id
            LEFT JOIN resource_resource rr ON rr.user_id = wo.mechanic_id
            LEFT JOIN res_company branch ON wo.company_id = branch.id
            WHERE wo.state IN ('sale', 'done') 
            AND (wo.open_date + interval '7 hours')::date BETWEEN {query_where}
            AND wo.company_id {query_company_id}
            GROUP BY  branch.id,wo.mechanic_id,rr.id
        """ 
        self._cr.execute (query)
        ress = self._cr.dictfetchall()
        return ress