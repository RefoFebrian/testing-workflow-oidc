#-*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import json
import logging

from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import valid_response, invalid_response, check_sensitive_value
from odoo.addons.rest_api.controllers.main import check_valid_token

# 3:  imports of odoo

from odoo import _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)

class ControllerREST(http.Controller):
    @http.route('/api/expedition/<version>/get_details', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_details(self, **post):
        url = str(request.httprequest.url).split('/api/')[0]
        picking_id = int(post.get('picking_id'))
        if not picking_id:
            return invalid_response(400, 'Mandatory Parameter Not Found', 'Parameter picking_id tidak ada.')

        query = f"""
            SELECT
                pick.id as picking_id,
                pick.name as picking_number,
                TO_CHAR(pick.validate_date, 'YYYY-MM-DD HH24:MI:SS') as validate_date,
                COALESCE(sum(move_line.quantity) FILTER(WHERE pp.division = 'Unit'),0) as total_unit,
                COALESCE(sum(move_line.quantity) FILTER(WHERE pp.division = 'Extras' OR pp.division IS NULL OR pp.division = ''),0) as total_extras,
                CASE
                    WHEN pick.filename_upload_image is not null THEN
                        '{url}' || '/web/content/stock.picking/' || {str(picking_id)} || '/file_image_show'
                    ELSE
                        NULL
                END as file_image,
                COALESCE(jsonb_agg(
                    DISTINCT jsonb_build_object(
                        'move_line_id', move_line.id,
                        'serial_number', lot.name,
                        'chassis_number', lot.chassis_number,
                        'product_name', '[' || pt.default_code::text || ']' || (pt.name::jsonb ->> 'en_US')::text
                    )
                ) FILTER (WHERE pp.division = 'Unit'), '[]') as unit,
                COALESCE(jsonb_agg(
                    DISTINCT jsonb_build_object(
                        'move_line_id', move_line.id,
                        'product_name', '[' || pt.default_code::text || ']' || (pt.name::jsonb ->> 'en_US')::text,
                        'quantity', move_line.quantity,
                        'actual_quantity', move_line.actual_quantity
                    )
                ) FILTER (WHERE pp.division = 'Extras' OR pp.division IS NULL OR pp.division = ''), '[]') AS extras
            FROM stock_move_line move_line
            JOIN stock_move move ON move.id = move_line.move_id
            JOIN stock_picking pick ON pick.id = move.picking_id
            JOIN product_product pp ON pp.id = move.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN stock_lot lot ON lot.id = move_line.lot_id
            WHERE pick.id = {picking_id}
            GROUP BY pick.id, pick.name, move_line.quantity, pick.validate_date, pick.filename_upload_image
        """
        try:
            request._cr.execute(query)
            ress = request._cr.dictfetchone()
            data = ress if ress else []
            return valid_response(200, data)
        except Exception as e:
            messsage = f"Error in get_details: {str(e)}"
            _logger.error(messsage)
            return invalid_response(400, 'data_not_found', messsage, 'GET')