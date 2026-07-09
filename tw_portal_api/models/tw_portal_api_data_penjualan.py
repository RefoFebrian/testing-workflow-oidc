#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from odoo import fields, http
from odoo.http import request
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response
from odoo.addons.rest_api.controllers.main import check_valid_token

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

    @http.route('/api/tw_portal_api/v1/get_portal_penjualan_dealer', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_portal_penjualan_dealer(self, **params):
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        if not start_date or not end_date:
            return invalid_response(400, 'Bad Request', "Parameter 'start_date' dan 'end_date' tidak boleh kosong!")

        try:
            start_date = fields.Date.to_date(start_date)
            end_date = fields.Date.to_date(end_date)
            if start_date > end_date:
                return invalid_response(400, 'Bad Request', 'start_date tidak boleh lebih besar dari end_date')

            product_name = self._sql_text_expression('product.template', 'product_tmpl', 'name')
            categ_name = self._sql_text_expression('product.category', 'prod_category', 'name')

            query = """
                SELECT
                    TO_CHAR((so.date_order + INTERVAL '7 hours')::date, 'YYYY-MM-DD') AS tanggal,
                    COALESCE(invoice.no_invoice, '') AS no_invoice,
                    COALESCE(customer.code, '') AS kode_dealer,
                    COALESCE(customer.name, '') AS nama_dealer,
                    %(product_name)s AS kode_part,
                    COALESCE(product.default_code, '') AS deskripsi,
                    %(categ_name)s AS subkat,
                    COALESCE(sol.product_uom_qty, 0) AS qty,
                    COALESCE(sol.cogs, 0) AS hpp,
                    COALESCE(sol.cogs, 0) * COALESCE(sol.product_uom_qty, 0) AS total_hpp,
                    COALESCE(sol.discount, 0) AS diskon
                FROM tw_sale_order so
                INNER JOIN tw_sale_order_line sol ON sol.order_id = so.id
                INNER JOIN res_company company ON company.id = so.company_id
                INNER JOIN tw_selection branch_type ON branch_type.id = company.branch_type_id
                    AND branch_type.type = 'BranchType'
                    AND branch_type.value = 'MD'
                LEFT JOIN res_partner customer ON customer.id = so.partner_id
                LEFT JOIN product_product product ON product.id = sol.product_id
                LEFT JOIN product_template product_tmpl ON product_tmpl.id = product.product_tmpl_id
                LEFT JOIN product_category prod_category ON prod_category.id = product_tmpl.categ_id
                LEFT JOIN LATERAL (
                    SELECT STRING_AGG(DISTINCT account_move.name, ', ' ORDER BY account_move.name) AS no_invoice
                    FROM tw_sale_order_line_invoice_rel rel
                    INNER JOIN account_move_line move_line ON move_line.id = rel.invoice_line_id
                    INNER JOIN account_move account_move ON account_move.id = move_line.move_id
                    WHERE rel.order_line_id = sol.id
                    AND account_move.state != 'draft'
                    AND account_move.move_type = 'out_invoice'
                ) invoice ON TRUE
                WHERE so.division = 'Sparepart'
                AND so.state IN ('sale', 'done')
                AND sol.display_type IS NULL
                AND COALESCE(sol.product_uom_qty, 0) != 0
                AND (so.date_order + INTERVAL '7 hours')::date >= %%s
                AND (so.date_order + INTERVAL '7 hours')::date <= %%s
                ORDER BY so.date_order ASC, so.name ASC, sol.id ASC
            """ % {
                'product_name': product_name,
                'categ_name': categ_name,
            }
            request._cr.execute(query, (start_date, end_date))
            ress = request._cr.dictfetchall()
            return valid_response(status=200, data=ress)
        except Exception as err:
            _logger.exception("Failed to get portal penjualan dealer")
            return invalid_response(400, 'Bad Request', str(err))

    @http.route('/api/tw_portal_api/v1/get_portal_penjualan_cabang', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_portal_penjualan_cabang(self, **params):
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        if not start_date or not end_date:
            return invalid_response(400, 'Bad Request', "Parameter 'start_date' dan 'end_date' tidak boleh kosong!")

        try:
            start_date = fields.Date.to_date(start_date)
            end_date = fields.Date.to_date(end_date)
            if start_date > end_date:
                return invalid_response(400, 'Bad Request', 'start_date tidak boleh lebih besar dari end_date')

            product_name = self._sql_text_expression('product.template', 'product_tmpl', 'name')
            categ_name = self._sql_text_expression('product.category', 'prod_cat', 'name')

            query = """
                SELECT
                    TO_CHAR(sd.date, 'YYYY-MM-DD') AS tanggal,
                    COALESCE(sd.name, '') AS no_invoice,
                    COALESCE(dealer.code, '') AS kode_dealer,
                    COALESCE(dealer.name, '') AS nama_dealer,
                    %(product_name)s AS kode_part,
                    COALESCE(product.default_code, '') AS deskripsi,
                    %(categ_name)s AS subkat,
                    COALESCE(sdl.qty, 0) AS qty,
                    COALESCE(sdl.supply_qty, 0) AS supplied_qty,
                    COALESCE(
                        NULLIF(mutation_line.initial_cogs, 0),
                        NULLIF(sale_line.cogs, 0),
                        CAST(product.standard_price ->> CAST(company.id AS TEXT) AS FLOAT),
                        0
                    ) AS hpp
                FROM tw_stock_distribution sd
                INNER JOIN res_company company ON company.id = sd.company_id
                INNER JOIN tw_selection branch_type ON branch_type.id = company.branch_type_id
                    AND branch_type.type = 'BranchType'
                    AND branch_type.value = 'MD'
                LEFT JOIN res_partner dealer ON dealer.id = sd.requester_id
                LEFT JOIN tw_stock_distribution_line sdl ON sdl.stock_distribution_id = sd.id
                LEFT JOIN product_product product ON product.id = sdl.product_id
                LEFT JOIN product_template product_tmpl ON product_tmpl.id = product.product_tmpl_id
                LEFT JOIN product_category prod_cat ON prod_cat.id = product_tmpl.categ_id
                LEFT JOIN LATERAL (
                    SELECT mol.initial_cogs
                    FROM tw_mutation_order mo
                    INNER JOIN tw_mutation_order_line mol ON mol.mutation_order_id = mo.id
                    WHERE mo.stock_distribution_id = sd.id
                    AND mol.product_id = sdl.product_id
                    ORDER BY mol.id DESC
                    LIMIT 1
                ) mutation_line ON TRUE
                LEFT JOIN LATERAL (
                    SELECT sol.cogs
                    FROM tw_sale_order so
                    INNER JOIN tw_sale_order_line sol ON sol.order_id = so.id
                    WHERE so.stock_distribution_id = sd.id
                    AND sol.product_id = sdl.product_id
                    AND sol.display_type IS NULL
                    ORDER BY sol.id DESC
                    LIMIT 1
                ) sale_line ON TRUE
                WHERE sd.division = 'Sparepart'
                AND sd.requester_id IS NOT NULL
                AND sd.state IN ('open', 'done', 'closed')
                AND sd.date >= %%s
                AND sd.date <= %%s
                ORDER BY sd.date ASC, sd.name ASC, sdl.id ASC
            """ % {
                'product_name': product_name,
                'categ_name': categ_name,
            }
            request._cr.execute(query, (start_date, end_date))
            ress = request._cr.dictfetchall()
            return valid_response(status=200, data=ress)
        except Exception as err:
            _logger.exception("Failed to get portal penjualan cabang")
            return invalid_response(400, 'Bad Request', str(err))
