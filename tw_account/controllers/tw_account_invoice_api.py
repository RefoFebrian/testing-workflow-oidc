#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import functools
import werkzeug.wrappers
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response 
from odoo.addons.rest_api.controllers.main import check_valid_token, valid_response
# 3:  imports of odoo
import odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

class ControllerREST(http.Controller):

    def _sql_text_expression(self, model_name, alias, field_name):
        lang = (request.env.context.get('lang') or 'en_US').replace("'", "''")
        field = request.env[model_name]._fields.get(field_name)
        if field and getattr(field, 'translate', False):
            return "COALESCE(%s.%s->>'%s', %s.%s->>'en_US', '')" % (
                alias, field_name, lang, alias, field_name
            )
        return "COALESCE(%s.%s::text, '')" % (alias, field_name)

    @http.route('/api/tw_account/v1/get_detail_invoice/', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_detail_account_invoice(self, **params):
        get_no_wo = params.get('no_wo')
        get_no_hp = params.get('no_hp')
        get_tgl_invoice = params.get('tgl_invoice')

        if not get_no_wo and not get_no_hp:
            return invalid_response(400, 'Bad Request', "Parameter 'no_wo' atau 'no_hp' tidak boleh kosong!")

        query_where = []
        query_params = []
        if get_no_wo:
            query_where.append("AND wo.name = %s")
            query_params.append(get_no_wo)
        if get_no_hp:
            query_where.append("AND wo.mobile = %s")
            query_params.append(get_no_hp)
        if get_tgl_invoice:
            try:
                invoice_date = fields.Date.to_date(get_tgl_invoice)
            except Exception:
                invoice_date = False
            if not invoice_date:
                return invalid_response(400, 'Bad Request', "Format parameter 'tgl_invoice' tidak valid!")
            query_where.append("AND invoice.invoice_date = %s")
            query_params.append(invoice_date)

        branch_name = self._sql_text_expression('res.company', 'branch', 'name')
        customer_name = self._sql_text_expression('res.partner', 'customer', 'name')
        journal_name = self._sql_text_expression('account.journal', 'journal', 'name')
        account_name = self._sql_text_expression('account.account', 'account', 'name')
        product_name = self._sql_text_expression('product.template', 'product_tmpl', 'name')

        query = """
            SELECT
                invoice.id AS invoice_id,
                branch.id AS branch_id,
                %(branch_name)s AS branch_name,
                invoice.name AS name_invoice,
                wo.name AS no_wo,
                wo.plate_number AS no_plat,
                wo.order_id AS order_id,
                customer.id AS customer_id,
                %(customer_name)s AS customer_name,
                invoice.division AS division,
                TO_CHAR(invoice.invoice_date, 'YYYY-MM-DD') AS date_invoice,
                journal.id AS journal_id,
                %(journal_name)s AS journal,
                account.id AS account_id,
                CASE
                    WHEN account.id IS NOT NULL THEN COALESCE(
                        account.code_store->>(branch.id::text),
                        account.code_store->>'1',
                        ''
                    ) || ' - ' || %(account_name)s
                    ELSE ''
                END AS account,
                invoice.amount_untaxed AS amount_untaxed,
                invoice.amount_total AS amount_total,
                invoice.amount_tax AS amount_tax,
                COALESCE(
                    jsonb_agg(DISTINCT jsonb_build_object(
                        'invoice_line_id', invoice_line.id,
                        'price_unit', invoice_line.price_unit,
                        'qty', invoice_line.quantity,
                        'product_code', COALESCE(product.default_code, ''),
                        'product_name', %(product_name)s
                    )) FILTER (WHERE invoice_line.id IS NOT NULL),
                    '[]'::jsonb
                ) AS work_lines
            FROM account_move invoice
            INNER JOIN account_move_line invoice_line ON invoice_line.move_id = invoice.id
                AND invoice_line.display_type = 'product'
                AND invoice_line.product_id IS NOT NULL
            INNER JOIN tw_work_order_line_invoice_rel wo_line_rel ON wo_line_rel.invoice_line_id = invoice_line.id
            INNER JOIN tw_work_order_line wo_line ON wo_line.id = wo_line_rel.order_line_id
            INNER JOIN tw_work_order wo ON wo.id = wo_line.order_id
            INNER JOIN tw_selection wo_type ON wo_type.id = wo.type_id
            LEFT JOIN res_company branch ON branch.id = invoice.company_id
            LEFT JOIN res_partner customer ON customer.id = invoice.partner_id
            LEFT JOIN account_journal journal ON journal.id = invoice.journal_id
            LEFT JOIN LATERAL (
                SELECT line.account_id
                FROM account_move_line line
                WHERE line.move_id = invoice.id
                AND line.display_type = 'payment_term'
                AND line.account_id IS NOT NULL
                ORDER BY line.id
                LIMIT 1
            ) payment_term_line ON TRUE
            LEFT JOIN account_account account ON account.id = payment_term_line.account_id
            LEFT JOIN product_product product ON product.id = invoice_line.product_id
            LEFT JOIN product_template product_tmpl ON product_tmpl.id = product.product_tmpl_id
            WHERE invoice.move_type = 'out_invoice'
            AND invoice.division = 'Sparepart'
            AND invoice.state = 'posted'
            AND invoice.payment_state IN ('not_paid', 'partial')
            AND wo_type.value IN ('REG', 'SLS', 'HOTLINE')
            AND COALESCE(wo.order_id, '') = ''
            %(query_where)s
            GROUP BY
                invoice.id,
                branch.id,
                wo.id,
                customer.id,
                journal.id,
                account.id
            ORDER BY invoice.invoice_date DESC, invoice.id DESC
        """ % {
            'branch_name': branch_name,
            'customer_name': customer_name,
            'journal_name': journal_name,
            'account_name': account_name,
            'product_name': product_name,
            'query_where': '\n'.join(query_where),
        }

        request._cr.execute(query, tuple(query_params))
        response = request._cr.dictfetchall()

        data = {
            'status': 200,
            'message': 'success',
            'response': response,
        }
        return valid_response(status=200, data=data)
