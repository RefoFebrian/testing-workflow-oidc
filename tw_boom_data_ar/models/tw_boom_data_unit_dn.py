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

class TWBoomDataARDN(models.Model):
    _inherit = "tw.boom.task"
    _description = "TW Boom Data AR DN"
    _order = "id desc"
    
    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields    
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    def schedule_generate_data_ar_unit_dn(self, limit=100, start_date=None, end_date=None, branch_code=None, source_transaksi=None, no_transaksi=None):
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
            query_date += "AND (tor.write_date + INTERVAL '7 HOURS')::DATE BETWEEN '{start_date}' AND '{end_date}'".format(start_date=start_date, end_date=end_date)
        else:
            query_date += "AND (tor.confirm_date IS NOT NULL AND ((tor.write_date + INTERVAL '7 HOURS')::DATE >= (NOW() - INTERVAL '1 DAYS')::DATE)"

        if source_transaksi:
            query_where += "AND ai.ref = '{}'".format(source_transaksi)

        if no_transaksi:
            query_where += "AND ai.name = '{}'".format(no_transaksi)

        if limit:
            query_limit += "LIMIT {}".format(limit)

        query = """
            select 
                b.id AS company_id
                , 'Pelunasan Other Receiveable (DN)' AS kategori
                , NULL AS finco_id
                , NULL AS customer_id
                , NULL AS product_id
                , NULL AS product_color_id
                , NULL AS lot_id
                , tor.id AS transaction_id
                , 'tw.other.receivable' AS model_name
                , NULL AS source_transaksi
                , tor.name AS no_transaksi
                , TO_CHAR(tor.create_date, 'YYYY-MM-DD HH24:MI:SS') AS tgl_transaksi
                , tor.due_date AS tgl_due_date_transaksi
                , tor.amount AS value
                , CASE WHEN tor.state = 'posted' THEN TO_CHAR(tor.write_date, 'YYYY-MM-DD HH24:MI:SS') ELSE NULL END AS done_date
                , CASE WHEN tor.state = 'posted' THEN 'done' ELSE 'open' END AS state
            FROM tw_other_receivable tor 
            LEFT JOIN res_company b on b.id = tor.company_id 
            LEFT JOIN tw_boom_task boom ON boom.no_transaction = tor.name AND boom.state = CASE WHEN tor.state = 'posted' THEN 'done' ELSE 'open' END
            WHERE 1=1
            AND boom.id IS NULL
            AND tor.state IN ('waiting_for_approval', 'posted')
            {query_branch}
            {query_date}
            {query_where}
            {query_limit}
        """.format(
            query_branch=query_branch,
            query_date=query_date,
            query_where=query_where,
            query_limit=query_limit,
        )

        self._cr.execute(query)
        result = self._cr.dictfetchall()

        if result:
            summary = self.suspend_security()._create_boom_task(result)
            
