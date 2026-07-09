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

class TWBoomDataStockAgingBPKB(models.Model):
    _inherit = "tw.boom.task"
    _description = "TW Boom Data STOCK Aging BPKB"
    _order = "id desc"
    
    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields    
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    def schedule_generate_data_stock_aging_bpkb_cash_perorang_current(self, limit=100, start_date=None, end_date=None, branch_code=None, source_transaksi=None, no_transaksi=None):
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
            query_date += " AND (lot.vehicle_ownership_receipt_date + INTERVAL '7 HOURS')::DATE BETWEEN '{start_date}' AND '{end_date}'".format(start_date=start_date, end_date=end_date)

        if source_transaksi:
            query_where += "AND lot.name = '{}'".format(source_transaksi)

        if no_transaksi:
            query_where += "AND stnk.name = '{}'".format(no_transaksi)

        if limit:
            query_limit += "LIMIT {}".format(limit)

        query = """
            SELECT 
                branch.id AS company_id
                , 'Aging Stock BPKB Cash - Perorangan (Current)' AS kategori
                , NULL AS product_id
                , NULL AS product_color_id
                , NULL AS lot_id
                , NULL AS finco_id
                , NULL AS customer_id
                , 'stock.lot' AS model_name
                , lot.id AS transaction_id
                , bpkb.name AS no_transaksi
                , lot.ownership_handover_date done_date
                , lot.vehicle_ownership_receipt_date AS tgl_transaksi
                , 1 AS value
                , lot.name AS source_transaksi
                , CASE WHEN lot.ownership_handover_date IS NULL THEN 'open' ELSE 'done' END AS state
            FROM stock_lot as lot
            LEFT JOIN tw_vehicle_ownership_receipt bpkb ON bpkb.id = lot.vehicle_ownership_receipt_id 
            LEFT JOIN tw_vehicle_document_location lokasi_bpkb ON lokasi_bpkb.id = bpkb.vehicle_ownership_location_id 
                AND lokasi_bpkb.document_type = 'vehicle_ownership'
            LEFT JOIN res_company branch ON branch.id = lot.company_id 
            LEFT JOIN tw_partner_cdb cddb on cddb.id = lot.cdb_partner_id  
            left join tw_selection payment_type on lot.payment_type_id = payment_type.id
            left join tw_selection cdb_cust_code on cddb.customer_code_id = cdb_cust_code.id
            LEFT JOIN tw_boom_task tab ON tab.no_transaction = bpkb.name AND tab.source_transaction = lot.name AND tab.state = 'open'
            WHERE 1=1
            AND payment_type.value = 'Cash'
            AND cdb_cust_code.value = 'I'
            {query_date}
            {query_branch}
            {query_where}
            AND (lot.vehicle_ownership_receipt_id IS NOT NULL OR lot.vehicle_ownership_receipt_date IS NOT NULL)
            AND ((lot.ownership_handover_date IS NULL) OR (lot.ownership_handover_date IS NOT NULL) OR tab.id notnull)
            AND lot.biro_jasa_id IS NOT NULL
            AND bpkb.name IS NOT NULL
            AND lokasi_bpkb.name NOT SIMILAR TO '%(Revisi|HHO|BRANKAS GA-RD)%'
            AND NOT EXISTS (
                SELECT 1
                FROM tw_boom_task boom
                WHERE boom.no_transaction = bpkb.name 
                AND boom.source_transaction = lot.name
                AND boom.state = CASE WHEN lot.ownership_handover_date IS NULL THEN 'open' ELSE 'done' END
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
            _logger.info(f"Cron schedule_generate_data_stock_aging_bpkb_cash_perorang_current completed: {summary}")


    def schedule_generate_data_stock_aging_bpkb_cash_instansi_current(self, limit=100, start_date=None, end_date=None, branch_code=None, source_transaksi=None, no_transaksi=None):
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
            query_date += " AND (lot.vehicle_ownership_receipt_date + INTERVAL '7 HOURS')::DATE BETWEEN '{start_date}' AND '{end_date}'".format(start_date=start_date, end_date=end_date)

        if source_transaksi:
            query_where += "AND lot.name = '{}'".format(source_transaksi)

        if no_transaksi:
            query_where += "AND bpkb.name = '{}'".format(no_transaksi)

        if limit:
            query_limit += "LIMIT {}".format(limit)

        query = """
            SELECT 
                branch.id AS company_id
                , 'Aging Stock BPKB Cash - Perusahaan/Instansi (Current)' AS kategori
                , NULL AS product_id
                , NULL AS product_color_id
                , NULL AS lot_id
                , NULL AS finco_id
                , NULL AS customer_id
                , 'stock.lot' AS model_name
                , lot.id AS transaction_id
                , bpkb.name AS no_transaksi
                , lot.ownership_handover_date date_done
                , lot.vehicle_ownership_receipt_date AS tgl_transaksi
                , 1 AS value
                , lot.name AS source_transaksi
                , CASE WHEN lot.ownership_handover_date IS NULL THEN 'open' ELSE 'done' END AS state
            FROM stock_lot as lot
            LEFT JOIN tw_vehicle_ownership_receipt bpkb ON bpkb.id = lot.vehicle_ownership_receipt_id 
            LEFT JOIN tw_vehicle_document_location lokasi_bpkb ON lokasi_bpkb.id = bpkb.vehicle_ownership_location_id 
                AND lokasi_bpkb.document_type = 'vehicle_ownership'
            LEFT JOIN res_company branch ON branch.id = lot.company_id 
            LEFT JOIN tw_partner_cdb cddb on cddb.id = lot.cdb_partner_id  
            left join tw_selection payment_type on lot.payment_type_id = payment_type.id
            left join tw_selection cdb_cust_code on cddb.customer_code_id = cdb_cust_code.id
            LEFT JOIN tw_boom_task tab ON tab.no_transaction = bpkb.name AND tab.source_transaction = lot.name AND tab.state = 'open'
            WHERE 1=1
            AND payment_type.value = 'Cash'
            AND cdb_cust_code.value = 'G'
            {query_date}
            {query_branch}
            {query_where}
            AND (lot.vehicle_ownership_receipt_id IS NOT NULL OR lot.vehicle_ownership_receipt_date IS NOT NULL)
            AND ((lot.ownership_handover_date IS NULL) OR (lot.ownership_handover_date IS NOT NULL) OR tab.id notnull)
            AND lot.biro_jasa_id IS NOT NULL
            AND bpkb.name IS NOT NULL
            AND lokasi_bpkb.name NOT SIMILAR TO '%(Revisi|HHO|BRANKAS GA-RD)%'
            AND NOT EXISTS (
                SELECT 1
                FROM tw_boom_task boom
                WHERE boom.no_transaction = bpkb.name 
                AND boom.source_transaction = lot.name
                AND boom.state = CASE WHEN lot.ownership_handover_date IS NULL THEN 'open' ELSE 'done' END
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
            _logger.info(f"Cron schedule_generate_data_stock_aging_bpkb_cash_instansi_current completed: {summary}")


    def schedule_generate_data_stock_aging_bpkb_credit_current(self, limit=100, start_date=None, end_date=None, branch_code=None, source_transaksi=None, no_transaksi=None):
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
            query_date += " AND (lot.vehicle_ownership_receipt_date + INTERVAL '7 HOURS')::DATE BETWEEN '{start_date}' AND '{end_date}'".format(start_date=start_date, end_date=end_date)

        if source_transaksi:
            query_where += "AND lot.name = '{}'".format(source_transaksi)

        if no_transaksi:
            query_where += "AND bpkb.name = '{}'".format(no_transaksi)

        if limit:
            query_limit += "LIMIT {}".format(limit)

        query = """
            SELECT 
                branch.id AS company_id
                , 'Aging Stock BPKB Credit (Current)' AS kategori
                , NULL AS product_id
                , NULL AS product_color_id
                , NULL AS lot_id
                , NULL AS finco_id
                , NULL AS customer_id
                , 'stock.lot' AS model_name
                , lot.id AS transaction_id
                , bpkb.name AS no_transaksi
                , lot.ownership_handover_date date_done
                , lot.vehicle_ownership_receipt_date AS tgl_transaksi
                , 1 AS value
                , lot.name AS source_transaksi
                , CASE WHEN lot.ownership_handover_date IS NULL THEN 'open' ELSE 'done' END AS state
            FROM stock_lot as lot
            LEFT JOIN tw_vehicle_ownership_receipt bpkb ON bpkb.id = lot.vehicle_ownership_receipt_id 
            LEFT JOIN tw_vehicle_document_location lokasi_bpkb ON lokasi_bpkb.id = bpkb.vehicle_ownership_location_id 
                AND lokasi_bpkb.document_type = 'vehicle_ownership'
            LEFT JOIN res_company branch ON branch.id = lot.company_id 
            LEFT JOIN tw_partner_cdb cddb on cddb.id = lot.cdb_partner_id  
            left join tw_selection payment_type on lot.payment_type_id = payment_type.id
            left join tw_selection cdb_cust_code on cddb.customer_code_id = cdb_cust_code.id
            LEFT JOIN tw_boom_task tab ON tab.no_transaction = bpkb.name AND tab.source_transaction = lot.name AND tab.state = 'open'
            WHERE 1=1
            AND payment_type.value = 'Credit'
            {query_date}
            {query_branch}
            {query_where}
            AND (lot.vehicle_ownership_receipt_id IS NOT NULL OR lot.vehicle_ownership_receipt_date IS NOT NULL)
            AND ((lot.ownership_handover_date IS NULL) OR (lot.ownership_handover_date IS NOT NULL) OR tab.id notnull)
            AND lot.biro_jasa_id IS NOT NULL
            AND bpkb.name IS NOT NULL
            AND lokasi_bpkb.name NOT SIMILAR TO '%(Revisi|HHO|BRANKAS GA-RD)%'
            AND NOT EXISTS (
                SELECT 1
                FROM tw_boom_task boom
                WHERE boom.no_transaction = bpkb.name 
                AND boom.source_transaction = lot.name
                AND boom.state = CASE WHEN lot.ownership_handover_date IS NULL THEN 'open' ELSE 'done' END
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


