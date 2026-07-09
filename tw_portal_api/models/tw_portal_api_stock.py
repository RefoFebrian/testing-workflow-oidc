#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from odoo import http
from odoo.http import request
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response
from odoo.addons.rest_api.controllers.main import check_valid_token

_logger = logging.getLogger(__name__)

class ControllerREST(http.Controller):

    def _get_branch_codes_param(self, params):
        branch_code = (params.get('branch_code') or '').strip()
        if not branch_code:
            return []
        return [code.strip() for code in branch_code.split(',') if code.strip()]

    def _sql_text_expression(self, model_name, alias, field_name):
        lang = (request.env.context.get('lang') or 'en_US').replace("'", "''")
        field = request.env[model_name]._fields.get(field_name)
        if field and getattr(field, 'translate', False):
            return "COALESCE(%s.%s->>'%s', %s.%s->>'en_US', '')" % (
                alias, field_name, lang, alias, field_name
            )
        return "COALESCE(%s.%s::text, '')" % (alias, field_name)

    def _get_stock_sparepart_query(self, branch_filter, include_kode_branch=False, include_area=False):
        product_name = self._sql_text_expression('product.template', 'product_tmpl', 'name')
        categ_name = self._sql_text_expression('product.category', 'categ', 'name')
        parent_categ_name = self._sql_text_expression('product.category', 'parent_categ', 'name')
        category = "COALESCE(NULLIF(%(categ_name)s, ''), NULLIF(%(parent_categ_name)s, ''), '')" % {
            'categ_name': categ_name,
            'parent_categ_name': parent_categ_name,
        }

        kode_branch_select = "company.code AS kode_branch," if include_kode_branch else ""
        area_select = ""
        area_group = ""
        area_outer_select = ""
        if include_area:
            area_select = """
                    , CASE
                        WHEN location.name IS NOT NULL THEN
                            CASE
                                WHEN location.name ILIKE '%%BL%%' THEN 'Belitung'
                                ELSE 'Bangka'
                            END
                        ELSE ''
                    END AS location_area
            """
            area_group = ", location.name"
            area_outer_select = ", quant.location_area AS area"

        return """
            SELECT
                %(kode_branch_select)s
                quant.default_code AS desc_part,
                quant.product_name AS kode_part,
                quant.categ_name AS kategori,
                quant.location_name AS lokasi
                %(area_outer_select)s,
                quant.qty_titipan,
                CASE
                    WHEN quant.location_usage = 'internal' THEN COALESCE((
                        SELECT SUM(move.product_uom_qty)
                        FROM stock_move move
                        LEFT JOIN stock_picking picking ON move.picking_id = picking.id
                        LEFT JOIN stock_picking_type picking_type ON picking.picking_type_id = picking_type.id
                        WHERE picking_type.code IN ('outgoing', 'interbranch_out')
                        AND picking.company_id = quant.company_id
                        AND picking.state NOT IN ('draft', 'cancel', 'done')
                        AND picking.division = 'Sparepart'
                        AND move.product_id = quant.product_id
                        AND move.location_id = quant.location_id
                    ), 0)
                    ELSE 0
                END AS qty_reserved,
                quant.qty_stock,
                COALESCE(
                    CAST(product.standard_price ->> CAST(quant.company_id AS TEXT) AS FLOAT),
                    0.01
                ) AS harga_satuan
            FROM (
                SELECT
                    COALESCE(location.company_id, quant.company_id) AS company_id,
                    location.complete_name AS location_name
                    %(area_select)s,
                    location.usage AS location_usage,
                    product.default_code,
                    %(product_name)s AS product_name,
                    %(category)s AS categ_name,
                    quant.product_id,
                    MIN(quant.in_date) AS in_date,
                    SUM(CASE WHEN quant.consolidated_date IS NULL THEN quant.quantity ELSE 0 END) AS qty_titipan,
                    SUM(CASE WHEN quant.consolidated_date IS NOT NULL THEN quant.quantity ELSE 0 END) AS qty_stock,
                    SUM(CASE WHEN quant.reserved_quantity > 0 THEN quant.reserved_quantity ELSE 0 END) AS qty_reserved,
                    quant.location_id
                FROM stock_quant quant
                INNER JOIN stock_location location ON quant.location_id = location.id
                    AND location.usage IN ('internal', 'transit', 'nrfs')
                LEFT JOIN product_product product ON quant.product_id = product.id
                LEFT JOIN product_template product_tmpl ON product.product_tmpl_id = product_tmpl.id
                LEFT JOIN product_category categ ON product_tmpl.categ_id = categ.id
                LEFT JOIN product_category parent_categ ON categ.parent_id = parent_categ.id
                WHERE COALESCE(product.division, product_tmpl.division) = 'Sparepart'
                GROUP BY
                    COALESCE(location.company_id, quant.company_id),
                    location.complete_name,
                    location.usage,
                    product.default_code,
                    product_tmpl.name,
                    categ.name,
                    parent_categ.name,
                    quant.product_id,
                    quant.location_id
                    %(area_group)s
            ) AS quant
            LEFT JOIN res_company company ON quant.company_id = company.id
            LEFT JOIN product_product product ON product.id = quant.product_id
            WHERE quant.location_usage IN ('internal', 'transit', 'nrfs')
            %(branch_filter)s
            ORDER BY quant.product_name, quant.location_name
        """ % {
            'kode_branch_select': kode_branch_select,
            'area_outer_select': area_outer_select,
            'area_select': area_select,
            'area_group': area_group,
            'product_name': product_name,
            'category': category,
            'branch_filter': branch_filter,
        }

    @http.route('/api/tw_portal_api/v1/get_stock_sparepart_md_and_cabang/', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_stock_sparepart_md_and_cabang(self, **params):
        try:
            branch_codes = self._get_branch_codes_param(params)
            branch_code_domain = [('code', 'in', branch_codes)] if branch_codes else []

            cab_asp = request.env['res.company'].sudo().search(
                [('branch_type_id.value', '=', 'DL')] + branch_code_domain
            )
            if not cab_asp and not branch_codes:
                return invalid_response(404, 'data_not_found', 'Data Cabang ASP')

            ress_cabang = []
            if cab_asp:
                query_cabang = self._get_stock_sparepart_query(
                    "AND quant.company_id = ANY(%s)",
                    include_kode_branch=True,
                )
                request._cr.execute(query_cabang, (cab_asp.ids,))
                ress_cabang = request._cr.dictfetchall()
            cabang_data = {
                'status': 1,
                'data': ress_cabang,
            }

            md_domain = [('branch_type_id.value', '=', 'MD')] + branch_code_domain
            md_limit = None if branch_codes else 1
            md = request.env['res.company'].sudo().search(md_domain, limit=md_limit)
            if not md and not branch_codes:
                return invalid_response(404, 'data_not_found', 'Data Main Dealer')
            if branch_codes and not cab_asp and not md:
                return invalid_response(404, 'data_not_found', 'Data Branch %s' % ', '.join(branch_codes))

            ress_md = []
            if md:
                query_md = self._get_stock_sparepart_query(
                    "AND quant.company_id = ANY(%s)",
                    include_area=True,
                )
                request._cr.execute(query_md, (md.ids,))
                ress_md = request._cr.dictfetchall()
            md_data = {
                'status': 1,
                'data': ress_md,
            }

            data = {
                'cabang': cabang_data,
                'md': md_data,
            }
            return valid_response(status=200, data=data)
        except Exception as err:
            _logger.exception("Failed to get stock sparepart MD and cabang")
            return invalid_response(400, 'bad_request', str(err))
