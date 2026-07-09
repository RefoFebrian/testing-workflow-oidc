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

class TWBoomDataStockAgingSTNK(models.Model):
    _inherit = "tw.boom.task"
    _description = "TW Boom Data STOCK Aging STNK"
    _order = "id desc"
    
    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields    
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    def schedule_generate_data_stock_aging_stnk_current(self, limit=100, start_date=None, end_date=None, branch_code=None, source_transaksi=None, no_transaksi=None):
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
            query_date += " AND (lot.vehicle_registration_receipt_date + INTERVAL '7 HOURS')::DATE BETWEEN '{start_date}' AND '{end_date}'".format(start_date=start_date, end_date=end_date)

        if source_transaksi:
            query_where += "AND lot.name = '{}'".format(source_transaksi)

        if no_transaksi:
            query_where += "AND stnk.name = '{}'".format(no_transaksi)

        if limit:
            query_limit += "LIMIT {}".format(limit)

        query = """
            SELECT
                branch.id AS company_id
                , 'Aging Stock STNK (Current)' AS kategori
                , NULL AS product_id
                , NULL AS product_color_id
                , NULL AS lot_id
                , NULL AS finco_id
                , NULL AS customer_id
                , 'stock.lot' AS model_name
                , lot.id AS transaction_id
                , stnk.name AS no_transaksi
                , lot.vehicle_registration_receipt_date AS tgl_transaksi
                , lot.registration_handover_date done_date
                , 1 AS value
                , lot.name AS source_transaksi
                , CASE WHEN lot.registration_handover_date IS NULL THEN 'open' ELSE 'done' END AS state
            FROM stock_lot lot
            LEFT JOIN tw_vehicle_registration_receipt stnk ON stnk.id = lot.vehicle_registration_receipt_id
            LEFT JOIN tw_vehicle_document_location lokasi_stnk ON lokasi_stnk.id = lot.vehicle_registration_location_id 
                AND lokasi_stnk.document_type = 'vehicle_registration'
            LEFT JOIN res_company branch ON branch.id = lot.company_id 
            LEFT JOIN tw_boom_task tab ON tab.no_transaction = stnk.name AND tab.source_transaction = lot.name AND tab.state = 'open'
            WHERE 1=1
            {query_date}
            {query_branch}
            {query_where}
            AND (lot.vehicle_registration_receipt_id IS NOT NULL OR lot.vehicle_registration_receipt_date IS NOT NULL)
            AND ((lot.registration_handover_id IS NULL OR lot.registration_handover_date IS NULL) OR tab.id NOTNULL)
            and lot.biro_jasa_id notnull
            and stnk."name" notnull
            and lokasi_stnk.name NOT SIMILAR TO '%(Revisi|HHO)%'
            AND NOT EXISTS (
                SELECT 1
                FROM tw_boom_task boom
                WHERE boom.no_transaction = stnk.name 
                AND boom.source_transaction = lot.name
                AND boom.state = CASE WHEN lot.registration_handover_date IS NULL THEN 'open' ELSE 'done' END
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
