# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from math import e 

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class ServiceRateReportProduct(models.TransientModel):
    _inherit = "tw.service.rate.report"
    _description = "Service Rate Report Product"

    def get_data_result(self):
        result = super().get_data_result()
        data_product = self._get_data_sr_product()
        result['Product'] = data_product

        return result

    def _get_data_sr_product(self):
        if self.start_date:
            start_date = self.start_date

        if self.end_date:
            end_date = self.end_date

        query = """
            SELECT 
                service_rate.name AS "Product"
                , service_rate.po_dms::numeric AS "PO DMS"
                , service_rate.mo::numeric AS "MO"
                , service_rate.supply::numeric AS "Supply"
                , CASE 
                    WHEN service_rate.mo != 0
                        THEN CONCAT(ROUND((service_rate.mo/service_rate.po_dms) * 100, 2)::varchar, '%')
                    ELSE '0.00%'
                END AS "PO x MO"
                , CASE 
                    WHEN service_rate.supply != 0
                        THEN CONCAT(ROUND((service_rate.supply / service_rate.po_dms) * 100, 2)::varchar, '%')
                    ELSE '0.00%'
                END AS "PO x SJ"
            FROM (
                SELECT
                    product.default_code AS name 
                    , SUM(COALESCE(sdl.requested_qty,0)) as po_dms
                    , SUM(COALESCE(sdl.supply_qty,0)) as mo
                    , SUM(COALESCE(sdl.supply_qty,0)) as supply
                FROM tw_stock_distribution AS sd
                LEFT JOIN tw_stock_distribution_line AS sdl ON sd.id = sdl.stock_distribution_id 
                LEFT JOIN product_product AS product ON sdl.product_id = product.id
                WHERE sd.division = 'Sparepart' AND product.default_code is not null
                AND sd.date::DATE BETWEEN '{start_date}' AND '{end_date}'
                AND (
                    sd.start_date::DATE BETWEEN
                    DATE_TRUNC('MONTH', '{start_date}'::DATE)::DATE
                    AND
                    (DATE_TRUNC('MONTH', '{end_date}'::DATE) + INTERVAL '1 MONTH' - INTERVAL '1 DAY')::DATE
                )
                AND (
                    sd.end_date::DATE BETWEEN
                    DATE_TRUNC('MONTH', '{start_date}'::DATE)::DATE
                    AND
                    (DATE_TRUNC('MONTH', '{end_date}'::DATE) + INTERVAL '1 MONTH' - INTERVAL '1 DAY')::DATE
                )
                AND sd.state in ('open', 'done', 'closed')
                AND sd.requester_id IS NOT NULL
                GROUP BY product.id
                order by product.default_code 
            ) AS service_rate
        """.format(start_date=start_date, end_date=end_date)
        
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        
        return result