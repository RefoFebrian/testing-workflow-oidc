#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json
import logging

from odoo import fields, http
from odoo.http import request

from odoo.addons.tw_api.controllers.main import invalid_response
from odoo.addons.rest_api.controllers.main import check_valid_token, valid_response

_logger = logging.getLogger(__name__)


class ControllerREST(http.Controller):

    def _sql_text_expression(self, model_name, alias, field_name):
        lang = (request.env.context.get('lang') or 'en_US').replace("'", "''")
        field = request.env[model_name]._fields.get(field_name)
        if field and getattr(field, 'translate', False):
            return "COALESCE(%s.%s->>'%s', %s.%s->>'en_US', '')" % (
                alias, field_name, lang, alias, field_name
            )
        return "COALESCE(%s.%s::text, '')" % (alias, field_name)

    @http.route('/api/tw_account/v1/get_list_invoice_sparepart/', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_list_invoice_sparepart(self, **params):
        partner_id = params.get('partner_id')
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        if not partner_id:
            return invalid_response(400, 'Bad Request', "Parameter 'partner_id' tidak boleh kosong!")
        if not start_date:
            return invalid_response(400, 'Bad Request', "Parameter 'start_date' tidak boleh kosong!")
        if not end_date:
            return invalid_response(400, 'Bad Request', "Parameter 'end_date' tidak boleh kosong!")

        try:
            partner_id = int(partner_id)
        except Exception:
            return invalid_response(400, 'Bad Request', "Format parameter 'partner_id' tidak valid!")

        try:
            date_from = fields.Date.to_date(start_date)
            date_to = fields.Date.to_date(end_date)
        except Exception:
            date_from = False
            date_to = False

        if not date_from:
            return invalid_response(400, 'Bad Request', "Format parameter 'start_date' tidak valid!")
        if not date_to:
            return invalid_response(400, 'Bad Request', "Format parameter 'end_date' tidak valid!")
        if date_from > date_to:
            return invalid_response(400, 'Bad Request', "Parameter 'start_date' tidak boleh lebih besar dari 'end_date'!")

        branch_name = self._sql_text_expression('res.company', 'branch', 'name')
        partner_name = self._sql_text_expression('res.partner', 'partner', 'name')

        query = """
            SELECT
                invoice.id,
                COALESCE(invoice.invoice_origin, '') AS origin,
                invoice.name AS number,
                invoice.company_id AS branch_id,
                %(branch_name)s AS branch_name,
                invoice.partner_id,
                %(partner_name)s AS partner_name,
                TO_CHAR(invoice.invoice_date, 'YYYY-MM-DD') AS date_invoice,
                TO_CHAR(invoice.invoice_date_due, 'YYYY-MM-DD') AS date_due,
                invoice.amount_untaxed,
                COALESCE(discount.discount_cash, 0) AS discount_cash,
                COALESCE(discount.discount_program, 0) AS discount_program,
                COALESCE(discount.discount_lain, 0) AS discount_lain,
                invoice.amount_tax,
                invoice.amount_total,
                invoice.amount_residual AS residual
            FROM account_move invoice
            LEFT JOIN res_partner partner ON partner.id = invoice.partner_id
            LEFT JOIN res_company branch ON branch.id = invoice.company_id
            LEFT JOIN LATERAL (
                SELECT
                    SUM(CASE WHEN account_discount.name = 'Discount Cash' THEN move_discount.amount ELSE 0 END) AS discount_cash,
                    SUM(CASE WHEN account_discount.name = 'Discount Program' THEN move_discount.amount ELSE 0 END) AS discount_program,
                    SUM(CASE WHEN account_discount.name = 'Discount Other' THEN move_discount.amount ELSE 0 END) AS discount_lain
                FROM account_move_discount move_discount
                INNER JOIN tw_account_discount account_discount
                    ON account_discount.id = move_discount.discount_id
                WHERE move_discount.move_id = invoice.id
            ) discount ON TRUE
            WHERE invoice.partner_id = %%s
              AND invoice.move_type = 'out_invoice'
              AND invoice.division = 'Sparepart'
              AND invoice.invoice_date >= %%s
              AND invoice.invoice_date <= %%s
            ORDER BY invoice.invoice_date ASC, invoice.id ASC
        """ % {
            'branch_name': branch_name,
            'partner_name': partner_name,
        }

        request._cr.execute(query, (partner_id, date_from, date_to))
        response = request._cr.dictfetchall()

        data = {
            'status': 200,
            'message': 'success',
            'response': response,
        }
        return valid_response(status=200, data=data)

    @http.route('/api/tw_account/v1/get_detail_invoice_sparepart/', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_detail_invoice_sparepart(self, **params):
        invoice_id = params.get('invoice_id')

        if not invoice_id:
            return invalid_response(400, 'Bad Request', "Parameter 'invoice_id' tidak boleh kosong!")

        try:
            invoice_id = int(invoice_id)
        except Exception:
            return invalid_response(400, 'Bad Request', "Format parameter 'invoice_id' tidak valid!")

        branch_name = self._sql_text_expression('res.company', 'branch', 'name')
        partner_name = self._sql_text_expression('res.partner', 'partner', 'name')
        distribution_name = self._sql_text_expression('tw.stock.distribution', 'distribution', 'name')
        distribution_description = self._sql_text_expression('tw.stock.distribution', 'distribution', 'description')
        po_type_name = self._sql_text_expression('tw.purchase.order.type', 'po_type', 'name')
        product_name = self._sql_text_expression('product.template', 'product_tmpl', 'name')

        query = """
            SELECT
                invoice.id AS invoice_id,
                COALESCE(invoice.invoice_origin, '') AS origin,
                invoice.name AS number,
                invoice.company_id AS branch_id,
                %(branch_name)s AS branch_name,
                invoice.partner_id,
                %(partner_name)s AS partner_name,
                partner.street AS partner_street,
                partner.no_npwp AS partner_npwp,
                TO_CHAR(invoice.invoice_date, 'YYYY-MM-DD') AS date_invoice,
                TO_CHAR(invoice.invoice_date_due, 'YYYY-MM-DD') AS date_due,
                invoice.amount_untaxed,
                COALESCE(discount.discount_cash, 0) AS discount_cash,
                COALESCE(discount.discount_program, 0) AS discount_program,
                COALESCE(discount.discount_lain, 0) AS discount_lain,
                invoice.amount_tax,
                invoice.amount_total,
                invoice.amount_residual AS residual,
                sale_order.id AS sale_order_id,
                sale_order.name AS sale_order_name,
                sale_order.stock_distribution_id AS distribution_id,
                distribution.id AS distribution_id,
                %(distribution_name)s AS distribution_name,
                distribution.purchase_order_type_id AS distribution_type_id,
                %(po_type_name)s AS tipe_po,
                %(distribution_description)s AS desc_po,
                invoice_line.id AS invoice_line_id,
                invoice_line.product_id,
                product.default_code AS product_code,
                %(product_name)s AS product_name,
                invoice_line.name AS line_description,
                invoice_line.price_unit,
                invoice_line.price_subtotal,
                invoice_line.quantity,
                invoice_line.discount
            FROM account_move invoice
            LEFT JOIN res_partner partner
                ON partner.id = invoice.partner_id
            LEFT JOIN res_company branch
                ON branch.id = invoice.company_id
            LEFT JOIN LATERAL (
                SELECT
                    SUM(CASE WHEN account_discount.name = 'Discount Cash' THEN move_discount.amount ELSE 0 END) AS discount_cash,
                    SUM(CASE WHEN account_discount.name = 'Discount Program' THEN move_discount.amount ELSE 0 END) AS discount_program,
                    SUM(CASE WHEN account_discount.name = 'Discount Other' THEN move_discount.amount ELSE 0 END) AS discount_lain
                FROM account_move_discount move_discount
                INNER JOIN tw_account_discount account_discount
                    ON account_discount.id = move_discount.discount_id
                WHERE move_discount.move_id = invoice.id
            ) discount ON TRUE
            LEFT JOIN LATERAL (
                SELECT so.*
                FROM tw_sale_order so
                WHERE so.name = invoice.invoice_origin
                   OR so.name = invoice.ref
                   OR EXISTS (
                        SELECT 1
                        FROM account_move_line rel_invoice_line
                        INNER JOIN tw_sale_order_line_invoice_rel sale_line_rel
                            ON sale_line_rel.invoice_line_id = rel_invoice_line.id
                        INNER JOIN tw_sale_order_line sale_line
                            ON sale_line.id = sale_line_rel.order_line_id
                        WHERE rel_invoice_line.move_id = invoice.id
                          AND sale_line.order_id = so.id
                   )
                ORDER BY
                    CASE
                        WHEN so.name = invoice.invoice_origin THEN 1
                        WHEN so.name = invoice.ref THEN 2
                        ELSE 3
                    END,
                    so.id
                LIMIT 1
            ) sale_order ON TRUE
            LEFT JOIN tw_stock_distribution distribution
                ON distribution.id = sale_order.stock_distribution_id
            LEFT JOIN tw_purchase_order_type po_type
                ON po_type.id = distribution.purchase_order_type_id
            LEFT JOIN account_move_line invoice_line
                ON invoice_line.move_id = invoice.id
               AND invoice_line.display_type = 'product'
            LEFT JOIN product_product product
                ON product.id = invoice_line.product_id
            LEFT JOIN product_template product_tmpl
                ON product_tmpl.id = product.product_tmpl_id
            WHERE invoice.id = %%s
            ORDER BY invoice_line.id
        """ % {
            'branch_name': branch_name,
            'partner_name': partner_name,
            'distribution_name': distribution_name,
            'distribution_description': distribution_description,
            'po_type_name': po_type_name,
            'product_name': product_name,
        }

        request._cr.execute(query, (invoice_id,))
        response = request._cr.dictfetchall()

        data = {
            'status': 200,
            'message': 'success',
            'response': response,
        }
        return valid_response(status=200, data=data)
