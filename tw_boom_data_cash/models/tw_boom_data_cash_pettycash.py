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

class TWBoomDataCashPettyCash(models.Model):
    _inherit = "tw.boom.task"
    _description = "TW Boom Data Cash Reimburse Petty Cash"
    _order = "id desc"
    
    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields    
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    def schedule_generate_data_cash_reimburse_petty_cash(self, limit=100, start_date=None, end_date=None, branch_code=None, source_transaksi=None, no_transaksi=None):
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
            query_date = " AND (wp.create_date + INTERVAL '7 HOURS')::DATE BETWEEN '{start_date}' AND '{end_date}'".format(start_date=start_date, end_date=end_date)

        if source_transaksi:
            query_where += "AND wp.name = '{}'".format(source_transaksi)

        if no_transaksi:
            query_where += "AND wp.name = '{}'".format(no_transaksi)

        if limit:
            query_limit += "LIMIT {}".format(limit)

        query = """
            SELECT 
                branch.id AS company_id
                , 'Reimburse Petty Cash' AS kategori
                , NULL AS finco_id
                , NULL AS customer_id
                , NULL AS product_id
                , NULL AS product_color_id
                , NULL AS lot_id
                , wp.id AS transaction_id
                , 'tw.petty.cash.out' AS model_name
                , wp.name AS source_transaksi
                , wp.name AS no_transaksi
                , TO_CHAR(wp.create_date, 'YYYY-MM-DD HH24:MI:SS') as tgl_transaksi
                , null as tgl_due_date_transaksi
                , wp.amount AS value
                , CASE WHEN wp.state = 'reimbursed' THEN TO_CHAR(wr.confirm_date, 'YYYY-MM-DD HH24:MI:SS') ELSE NULL END AS done_date
                , CASE WHEN wp.state = 'reimbursed' THEN 'done' ELSE 'open' END AS state
            FROM tw_petty_cash_out wp 
            LEFT JOIN tw_reimbursement_petty_cash wr ON wp.reimbursed_id = wr.id 
            LEFT JOIN res_company branch ON wp.company_id = branch.id 
            LEFT JOIN tw_boom_task boom ON boom.no_transaction = wp.name AND boom.state = CASE WHEN wp.state = 'reimbursed' THEN 'done' ELSE 'open' END
            WHERE 1=1
            AND wp.state NOT IN ('draft', 'cancel')
            AND boom.id IS NULL
            {query_date}
            {query_branch}
            {query_where}
            {query_limit}
        """.format(
            query_date=query_date,
            query_branch=query_branch,
            query_where=query_where,
            query_limit=query_limit
        )

        self._cr.execute(query)
        result = self._cr.dictfetchall()

        if result:
            summary = self.suspend_security()._create_boom_task(result)
