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

class TWBoomDataARWOClaim(models.Model):
    _inherit = "tw.boom.task"
    _description = "TW Boom Data AR WO Claim"
    _order = "id desc"
    
    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields    
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    def schedule_generate_data_ar_part_wo_claim(self, limit=100, start_date=None, end_date=None, branch_code=None, source_transaksi=None, no_transaksi=None):
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
            query_branch += "AND b.code = '%s'" % branch_code
        else:
            if list_branch_pilot:
                query_branch += "AND b.id = ANY(%s)" % str(list_branch_pilot)

        if start_date and end_date:
            query_date += "AND (ai.write_date + INTERVAL '7 HOURS')::DATE BETWEEN '{start_date}' AND '{end_date}'".format(start_date=start_date, end_date=end_date)
        else:
            query_date += "AND (ai.confirm_date IS NOT NULL AND ((ai.write_date + INTERVAL '7 HOURS')::DATE >= (NOW() - INTERVAL '1 DAYS')::DATE))"

        if source_transaksi:
            query_where += "AND ai.ref = '{}'".format(source_transaksi)

        if no_transaksi:
            query_where += "AND ai.name = '{}'".format(no_transaksi)

        if limit:
            query_limit += "LIMIT {}".format(limit)


        query = """
            SELECT
                b.id AS company_id
                , 'Pelunasan WO Claim' AS kategori
                , NULL as finco
                , NULL as customer_name
                , NULL as tipe_kendaraan
                , NULL as warna_kendaraan
                , NULL as no_mesin
                , ai.id AS transaction_id
                , 'account.move' AS model_name
                , COALESCE(ai.ref, ai.name) AS source_transaksi
                , ai.name AS no_transaksi
                , TO_CHAR(ai.create_date, 'YYYY-MM-DD HH24:MI:SS') AS tgl_transaksi
                , ai.invoice_date_due AS tgl_due_date_transaksi
                , ai.amount_total AS value
                , CASE WHEN ai.state = 'paid' THEN TO_CHAR(ai.write_date, 'YYYY-MM-DD HH24:MI:SS') ELSE NULL END AS done_date
                , CASE WHEN ai.state = 'paid' THEN 'done' ELSE 'open' END AS state
            FROM account_move ai
            LEFT JOIN account_journal aj ON ai.journal_id = aj.id
            LEFT JOIN tw_work_order wo ON ai.ref = wo."name" 
            LEFT JOIN res_company b ON ai.company_id = b.id
            LEFT JOIN tw_boom_task boom ON boom.no_transaction = ai.name AND boom.state = CASE WHEN ai.state = 'paid' THEN 'done' ELSE 'open' END
            WHERE 1=1
            AND boom.id IS NULL
            AND ai.move_type = 'out_invoice'
            AND wo.type = 'CLA'
            AND aj.name->>'en_US' = 'Journal WO Claim'
            {query_branch}
            {query_date}
            {query_where}
            {query_limit}
        """.format(
            query_where=query_where,
            query_date=query_date,
            query_branch=query_branch,
            query_limit=query_limit,
        )

        self._cr.execute(query)
        result = self._cr.dictfetchall()

        if result:
            summary = self.suspend_security()._create_boom_task(result)
