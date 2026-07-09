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

    @http.route('/api/tw_portal_api/v1/get_api_good_receipt_unit/', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_api_good_receipt_unit(self, **params):
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        if not start_date or not end_date:
            return invalid_response(400, 'Error', 'Mandatory [start_date, end_date]')

        try:
            start_date = fields.Date.to_date(start_date)
            end_date = fields.Date.to_date(end_date)
            if start_date > end_date:
                return invalid_response(400, 'Error', 'start_date tidak boleh lebih besar dari end_date')

            product_name = self._sql_text_expression('product.template', 'pt', 'name')
            product_description = self._sql_text_expression('product.template', 'pt', 'description')
            color_name = self._sql_text_expression('product.attribute.value', 'pav', 'name')
            attribute_name = self._sql_text_expression('product.attribute', 'pa', 'name')

            query = """
                SELECT
                    COALESCE(spb.name, '') AS packing_name,
                    COALESCE(spb.date::text, '') AS packing_date,
                    COALESCE(lot.name, bl.lot_name, '') AS engine_number,
                    COALESCE(lot.chassis_number, bl.chassis_number, '') AS chassis_number,
                    %(product_name)s AS prod_type,
                    COALESCE(pp.default_code, '') AS prod_marketing,
                    %(product_description)s AS prod_desc,
                    COALESCE(color.code, '') AS warna_code,
                    COALESCE(color.name, '') AS warna_desc
                FROM stock_picking_batch spb
                INNER JOIN res_company company ON company.id = spb.company_id
                INNER JOIN tw_selection branch_type ON branch_type.id = company.branch_type_id
                    AND branch_type.type = 'BranchType'
                    AND branch_type.value = 'MD'
                INNER JOIN stock_picking_type spt ON spt.id = spb.picking_type_id
                INNER JOIN tw_stock_picking_batch_line bl ON bl.batch_id = spb.id
                LEFT JOIN stock_lot lot ON lot.id = bl.lot_id
                INNER JOIN product_product pp ON pp.id = COALESCE(bl.product_id, lot.product_id)
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN LATERAL (
                    SELECT
                        pav.code,
                        %(color_name)s AS name
                    FROM product_variant_combination pvc
                    INNER JOIN product_template_attribute_value ptav
                        ON ptav.id = pvc.product_template_attribute_value_id
                    INNER JOIN product_attribute_value pav
                        ON pav.id = ptav.product_attribute_value_id
                    LEFT JOIN product_attribute pa
                        ON pa.id = ptav.attribute_id
                    WHERE pvc.product_product_id = pp.id
                    ORDER BY
                        CASE
                            WHEN %(attribute_name)s IN ('Color', 'Warna', 'Colour') THEN 0
                            ELSE 1
                        END,
                        pav.id
                    LIMIT 1
                ) color ON TRUE
                WHERE spt.code = 'incoming'
                AND UPPER(COALESCE(spt.sequence_code, '')) = 'IN'
                AND spb.state = 'done'
                AND spb.division = 'Unit'
                AND spb.type = 'MD'
                AND spb.date >= %%s
                AND spb.date <= %%s
                ORDER BY spb.date ASC, spb.name ASC, bl.sequence_number ASC, bl.id ASC
            """ % {
                'product_name': product_name,
                'product_description': product_description,
                'color_name': color_name,
                'attribute_name': attribute_name,
            }
            request._cr.execute(query, (start_date, end_date))
            ress = request._cr.dictfetchall()

            if not ress:
                return invalid_response(400, 'data_not_found', 'Data tidak ditemukan !')

            data = {
                'status': 200,
                'message': 'success',
                'response': ress,
            }
            return valid_response(status=200, data=data)
        except Exception as err:
            _logger.exception("Failed to get API good receipt unit")
            return invalid_response(400, 'bad_request', str(err))
