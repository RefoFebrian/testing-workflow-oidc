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

class TWBoomDataARSCP(models.Model):
    _inherit = "tw.boom.task"
    _description = "TW Boom Data AR SCP"
    _order = "id desc"
    
    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields    
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    def schedule_generate_data_ar_unit_scp(self, limit=100, start_date=None, end_date=None, branch_code=None, source_transaksi=None, no_transaksi=None):
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
                , 'Pelunasan Subsidi Program MD (SCP)' AS kategori
                , NULL AS product_id
                , NULL AS product_color_id
                , NULL AS lot_id
                , NULL AS finco_id
                , NULL AS customer_id
                , ai.id AS transaction_id
                , 'account.move' AS model_name
                , COALESCE(ai.ref, ai.name) AS source_transaksi
                , ai.name AS no_transaksi
                , TO_CHAR(ai.create_date, 'YYYY-MM-DD HH24:MI:SS') AS tgl_transaksi
                , ai.invoice_date_due AS tgl_due_date_transaksi
                , ai.amount_total AS value
                , CASE WHEN ai.payment_state = 'paid' THEN TO_CHAR(ai.write_date, 'YYYY-MM-DD HH24:MI:SS') ELSE NULL END AS done_date
                , CASE WHEN ai.payment_state = 'paid' THEN 'done' ELSE 'open' END AS state
            FROM account_move ai
            JOIN account_journal aj ON ai.journal_id = aj.id
            LEFT JOIN res_company b ON ai.company_id = b.id
            LEFT JOIN tw_dealer_sale_order dso ON ai.ref = dso.name
            LEFT JOIN tw_dealer_sale_order_line dsol on dsol.order_id = dso.id
            LEFT JOIN res_partner finco ON dso.finco_id = finco.id
            LEFT JOIN res_partner cust ON dso.partner_id = cust.id
            LEFT JOIN product_product pp on dsol.product_id = pp.id 
            LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id
            LEFT JOIN product_variant_combination as pvc on pvc.product_product_id = pp.id
            LEFT JOIN product_template_attribute_value as ptav on ptav.id = pvc.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            LEFT JOIN stock_lot lot on lot.id = dsol.lot_id
            LEFT JOIN tw_boom_task boom ON boom.no_transaction = ai.name AND boom.state = CASE WHEN ai.payment_state = 'paid' THEN 'done' ELSE 'open' END
            WHERE 1=1
            AND ai.division = 'Unit'
            AND dsol.lot_id notnull
            AND aj.name->>'en_US' = 'Journal PS MD'
            {query_where}
            {query_branch}
            {query_date}
            AND ai.move_type = 'out_invoice'
            AND NOT EXISTS(
                select 1
                from tw_boom_task boom
                where boom.no_transaction = ai.name 
                AND boom.source_transaction = ai.ref 
                and boom.state = CASE WHEN ai.payment_state = 'paid' THEN 'done' ELSE 'open' END
            )
            {query_limit}
        """.format(
            query_where=query_where, 
            query_date=query_date,
            query_limit=query_limit,
            query_branch=query_branch)

        self._cr.execute(query)
        result = self._cr.dictfetchall()

        if result:
            summary = self.suspend_security()._create_boom_task(result)
            

