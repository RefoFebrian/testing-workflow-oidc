# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib

class TWBoomDataStockOutstandingSTNK(models.Model):
    _inherit = "tw.boom.task"
    _description = "TW Boom Data STOCK Outstanding STNK"
    _order = "id desc"
    
    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields    
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    def _get_data_stock_outstanding_stnk_current(self, limit=100, start_date=None, end_date=None, branch_code=None, source_transaksi=None, no_transaksi=None):
        query_where = ""
        query_limit = ""
        query_date = ""
        query_branch = ""
        list_branch_pilot = []
        pilot_obj = self.env['tw.pilot.project'].sudo().search([
            ('active', '=', True),
            ('name','=','BOOM')])

        if pilot_obj:
            list_branch_pilot = eval(pilot_obj.company_id_result)

        if branch_code:
            query_branch += "AND branch.code = '%s'" % branch_code
        else:
            if list_branch_pilot:
                query_branch += "AND branch.id = ANY(%s)" % str(list_branch_pilot)

        if start_date and end_date:
            query_date += " AND (dso.confirm_date + INTERVAL '7 HOURS')::DATE BETWEEN '{start_date}' AND '{end_date}'".format(start_date=start_date, end_date=end_date)

        if source_transaksi:
            query_where += "AND lot.name = '{}'".format(source_transaksi)

        if no_transaksi:
            query_where += "AND dso.name = '{}'".format(no_transaksi)

        if limit:
            query_limit += "LIMIT {}".format(limit)

        query = """
            SELECT 
                branch.id AS company_id
                , 'Outstanding STNK (Belum Terima)' AS kategori
                , NULL AS product_id
                , NULL AS product_color_id
                , NULL AS lot_id
                , NULL AS finco_id
                , NULL AS customer_id
                , 'stock.lot' AS model_name
                , lot.id AS transaction_id
                , dso.name AS no_transaksi
                , to_char(dso.confirm_date, 'YYYY-MM-DD HH24:MI:SS') AS tgl_transaksi
                , 1 AS value
                , lot.name AS source_transaksi
                , CASE WHEN lot.vehicle_registration_receipt_date IS NOT NULL THEN to_char(stnk.confirm_date,'YYYY-MM-DD HH24:MI:SS') ELSE NULL END AS done_date
                , CASE 
                    WHEN lot.vehicle_registration_receipt_date IS NULL THEN 'open' 
                    ELSE 'done' 
                END AS state
            FROM stock_lot lot
            LEFT JOIN tw_vehicle_registration_receipt stnk ON stnk.id = lot.vehicle_registration_receipt_id 
            LEFT JOIN tw_dealer_sale_order dso ON lot.dealer_sale_order_id = dso.id
            LEFT JOIN res_company branch ON branch.id = dso.company_id 
            left join lateral (
                select boom.*
                from tw_boom_task boom 
                left join tw_boom_category tbc on tbc.id = boom.category_id
                where boom.no_transaction = dso.name 
                AND boom.source_transaction = lot.name 
                AND tbc.name = 'Outstanding STNK (Belum Terima)' 
                AND boom.state = 'open'
            ) tab on True
            WHERE 1=1
            AND lot.state != 'workshop'
            AND lot.biro_jasa_id IS NOT NULL
            AND dso.confirm_date IS NOT NULL 
            AND (tab.id notnull or lot.vehicle_registration_receipt_date is NULL)
            {query_date}
            {query_branch}
            {query_where}
            AND NOT EXISTS (
                SELECT 1
                FROM tw_boom_task boom
                WHERE boom.no_transaction = dso.name 
                AND boom.source_transaction = lot.name
                AND boom.state = CASE WHEN lot.vehicle_registration_receipt_date IS NULL THEN 'open' ELSE 'done' END
            )
            {query_limit}
        """.format(
            query_where=query_where, 
            query_date=query_date,
            query_branch=query_branch,
            query_limit=query_limit)

        self._cr.execute(query)
        result = self._cr.dictfetchall()

        if result:
            summary = self.suspend_security()._create_boom_task(result)

