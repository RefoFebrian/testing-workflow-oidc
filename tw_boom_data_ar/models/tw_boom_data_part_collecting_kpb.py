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

class TWBoomDataARCKKPB(models.Model):
    _inherit = "tw.boom.task"
    _description = "TW Boom Data AR CK KPB"
    _order = "id desc"
    
    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields    
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    def schedule_generate_data_ar_part_collecting_kpb(self, limit=100, start_date=None, end_date=None, branch_code=None, source_transaksi=None, no_transaksi=None):
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
            query_date += "AND (wck.write_date + INTERVAL '7 HOURS')::DATE BETWEEN '{start_date}' AND '{end_date}'".format(start_date=start_date, end_date=end_date)
        else:
            query_date += "AND ((wck.write_date + INTERVAL '7 HOURS')::DATE >= (NOW() - INTERVAL '1 DAYS')::DATE)"

        if no_transaksi:
            query_where += "AND wck.name = '{}'".format(no_transaksi)

        if limit:
            query_limit += "LIMIT {}".format(limit)

        query = """
            SELECT
                b.id AS company_id
                , 'Pelunasan Collecting KPB' AS kategori
                , NULL as finco
                , NULL as customer_name
                , NULL as tipe_kendaraan
                , NULL as warna_kendaraan
                , NULL as no_mesin
                , wck.id AS transaction_id
                , 'tw.work.order.collecting' AS model_name
                , NULL AS source_transaksi
                , wck.name AS no_transaksi
                , TO_CHAR(wck.create_date, 'YYYY-MM-DD HH24:MI:SS') AS tgl_transaksi
                , wck.due_date AS tgl_due_date_transaksi
                , CASE WHEN (SUM(aml.debit) - SUM(aml.credit)) = 0  THEN SUM(aml.debit) ELSE 0 END AS value
                , CASE WHEN wck.state = 'posted' THEN TO_CHAR(wck.confirm_date, 'YYYY-MM-DD HH24:MI:SS') ELSE NULL END AS done_date
                , CASE WHEN wck.state = 'posted' THEN 'done' ELSE 'open' END AS state
            FROM tw_work_order_collecting wck
            LEFT JOIN account_move am ON am.ref = wck.name
            LEFT JOIN account_move_line aml ON aml.move_id = am.id
            LEFT JOIN account_journal aj ON am.journal_id = aj.id
            LEFT JOIN res_company b ON wck.company_id = b.id
            LEFT JOIN tw_boom_task boom ON boom.no_transaction = wck.name AND boom.state = CASE WHEN wck.state = 'posted' THEN 'done' ELSE 'open' END
            WHERE 1=1
            AND boom.id IS NULL
            and wck."type" = 'KPB'
            and aj.name->>'en_US' = 'Journal Collecting KPB'
            {query_where}
            {query_date}
            {query_branch}
            GROUP BY b.id, b.name, wck.id, wck.name, wck.create_date, wck.due_date, wck.state, aj.name
            {query_limit}
        """.format(
            query_where=query_where,
            query_date=query_date,
            query_branch=query_branch,
            query_limit=query_limit
        )

        self._cr.execute(query)
        result = self._cr.dictfetchall()

        if result:
            summary = self.suspend_security()._create_boom_task(result)

