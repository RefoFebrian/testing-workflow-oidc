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

class ServiceRateReportBranch(models.TransientModel):
    _inherit = "tw.service.rate.report"
    _description = "Service Rate Report Branch"


    def get_data_result(self):
        result = super().get_data_result()
        data_branch = self._get_data_sr_branch()
        result['Branch'] = data_branch

        return result

    def _get_data_sr_branch(self):
        if self.start_date:
            start_date = self.start_date

        if self.end_date:
            end_date = self.end_date

        query = """
            SELECT 
                service_rate.name AS "Branch"
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
                    branch.code AS name  
                    , SUM(COALESCE(sdl.requested_qty,0)) AS po_dms
                    , SUM(COALESCE(sdl.supply_qty,0)) AS mo
                    , SUM(COALESCE(sdl.supply_qty,0)) AS supply
                FROM tw_stock_distribution AS sd
                LEFT JOIN tw_stock_distribution_line AS sdl ON sd.id = sdl.stock_distribution_id
                left join res_partner branch ON sd.requester_id = branch.id
                WHERE sd.division = 'Sparepart' AND branch.code IS NOT NULL
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
                GROUP BY branch.id
                ORDER BY branch.code
            ) AS service_rate
        """.format(start_date=start_date, end_date=end_date)

        self._cr.execute(query)
        result = self._cr.dictfetchall()
        
        return result