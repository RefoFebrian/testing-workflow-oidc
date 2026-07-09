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

    # Valid states whitelist for delivery_state filtering
    VALID_DELIVERY_STATES = {'intransit', 'draft', 'delivered'}
    # Maximum allowed limit for pagination
    MAX_LIMIT = 100

    @http.route('/api/expedition/<version>/get_picking_dashboard', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_picking_dashboard(self, **post):
        """Get dashboard summary counts for picking by delivery state.

        Returns a list of driver summaries with intransit, sent, and draft counts.
        Supports filtering by division and type (mutation, sale, mutation_asset, mutation_internal).
        """
        uid = request.session.uid
        division = post.get('division', 'Unit')

        # Build type condition (static values only, no user input interpolated)
        type_condition = ""
        type_filter = post.get('type', 'all')
        if type_filter == 'mutation':
            type_condition = "AND pick.mutation_order_id IS NOT NULL AND pick_type.code = 'outgoing'"
        elif type_filter == 'sale':
            type_condition = "AND (pick.sale_order_id IS NOT NULL or pick.dealer_sale_order_id IS NOT NULL)"
        elif type_filter == 'mutation_asset':
            # Override division for mutation_asset
            division = 'Umum'
            type_condition = "AND pick.origin ILIKE '%%MIA%%'"
        elif type_filter == 'mutation_internal':
            type_condition = "AND pick.name ILIKE '%%MU%%' AND (pick.origin NOT ILIKE '%%MIA%%' OR pick.origin IS NULL)"

        query = f"""
            SELECT
                emp.name as driver_name,
                COALESCE(SUM(
                    CASE
                        WHEN pick.delivery_state = 'intransit'
                            AND pp.division = 'Unit'
                            THEN move.quantity
                        WHEN pick.delivery_state = 'intransit'
                            AND pp.division = 'Umum'
                            AND pick.origin ILIKE '%%MIA%%'
                            THEN move.quantity * 4
                        ELSE 0
                    END
                ),0)::int AS total_intransit,
                COALESCE(SUM(
                    CASE
                        WHEN pick.delivery_state = 'delivered'
                            AND pp.division = 'Unit'
                            THEN move.quantity
                        WHEN pick.delivery_state = 'delivered'
                            AND pp.division = 'Umum'
                            AND pick.origin ILIKE '%%MIA%%'
                            THEN move.quantity * 4
                        ELSE 0
                    END
                ),0)::int AS total_sent,
                COALESCE(SUM(
                    CASE
                        WHEN pick.delivery_state = 'draft'
                            AND pp.division = 'Unit'
                            THEN move.quantity
                        WHEN pick.delivery_state = 'draft'
                            AND pp.division = 'Umum'
                            AND pick.origin ILIKE '%%MIA%%'
                            THEN move.quantity * 4
                        ELSE 0
                    END
                ),0)::int AS total_draft
            FROM stock_picking pick
            JOIN stock_picking_type pick_type ON pick_type.id = pick.picking_type_id
            JOIN stock_move move ON move.picking_id = pick.id
            LEFT JOIN product_product pp ON pp.id = move.product_id
            JOIN hr_employee emp ON emp.id = pick.delivery_driver_id
            WHERE 1=1
            AND pick.delivery_driver_id is not null
            AND pick.division = %s
            AND emp.user_id = {uid}
            {type_condition}
            GROUP BY emp.name
        """
        try:
            request._cr.execute(query, (division,))
            data = request._cr.dictfetchone()
            return valid_response(200, data if data else {})
        except Exception as e:
            message = f"Error in get_picking_dashboard: {str(e)}"
            _logger.error(message)
            return invalid_response(400, 'data_not_found', message, 'GET')

    @http.route('/api/expedition/<version>/get_picking_transit', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_picking_transit(self, **post):
        """Get list of picking in transit with filtering, searching, and pagination."""
        # --- Input validation ---
        uid = request.session.uid
        try:
            limit = min(int(post.get('limit', 10)), self.MAX_LIMIT)
            offset = int(post.get('offset', 0))
            if limit < 0 or offset < 0:
                raise ValueError("limit and offset must be non-negative")
        except (ValueError, TypeError) as e:
            return invalid_response(400, 'invalid_params', f'Invalid limit/offset: {str(e)}', 'GET')

        division = post.get('division', 'Unit')
        search = post.get('string', '')
        
        # --- State validation with whitelist ---
        state_default = ('intransit', 'draft', 'delivered')
        if 'state' in post:
            state_input = post['state']
            if isinstance(state_input, str):
                state_list = [state_input]
            elif isinstance(state_input, (list, tuple)):
                state_list = list(state_input)
            else:
                state_list = [str(state_input)]
            # Filter to only valid states
            state_list = [s for s in state_list if s in self.VALID_DELIVERY_STATES]
            if not state_list:
                state_list = list(state_default)
        else:
            state_list = list(state_default)

        # --- Build parameterized query parts ---
        params = []

        # State placeholders
        state_placeholders = ','.join(['%s'] * len(state_list))
        params.extend(state_list)

        # Division parameter
        params.append(division)

        # Type condition (static values only, no user input interpolated)
        type_condition = ""
        type_filter = post.get('type', 'all')
        if type_filter == 'mutation':
            type_condition = "AND pick.mutation_order_id IS NOT NULL AND pick_type.code = 'outgoing'"
        elif type_filter == 'sale':
            type_condition = "AND (pick.sale_order_id IS NOT NULL or pick.dealer_sale_order_id IS NOT NULL)"
        elif type_filter == 'mutation_asset':
            # Override division for mutation_asset
            params[-1] = 'Umum'
            type_condition = "AND pick.origin ILIKE '%%MIA%%'"
        elif type_filter == 'mutation_internal':
            type_condition = "AND pick.name ILIKE '%%MU%%' AND (pick.origin NOT ILIKE '%%MIA%%' OR pick.origin IS NULL)"

        # Search condition (parameterized)
        search_condition = ""
        if search:
            search_condition = "AND pick.name ILIKE %s"
            params.append(f'%{search}%')

        # Limit & Offset
        params.append(limit)
        params.append(offset)

        query = f"""
            SELECT
                pick.id as picking_id,
                pick.name as picking_name,
                COALESCE(pick.origin, pick.name) as source_dokumen,
                TO_CHAR(pick.validate_date, 'YYYY-MM-DD HH24:MI:SS') as date,
                branch.name as sending_dealer,
                partner.name as receive_dealer,
                CASE
                    WHEN pick.delivery_state = 'draft' THEN 'In Progress'
                    ELSE INITCAP(pick.delivery_state)
                END as delivery_state,
                emp.name as driver_name,
                (
                    COALESCE(SUM(
                        CASE
                            WHEN pp.division = 'Unit'
                                THEN sm.quantity
                            WHEN pp.division = 'Umum'
                                AND pick.origin ILIKE '%%MIA%%'
                                THEN sm.quantity * 4
                            ELSE 0
                        END
                    ),0)
                )::int AS total_unit
            FROM stock_picking pick
            INNER JOIN stock_move sm ON pick.id = sm.picking_id
            INNER JOIN stock_picking_type pick_type ON pick_type.id = pick.picking_type_id
            INNER JOIN res_company branch ON pick.company_id = branch.id
            LEFT JOIN product_product pp on pp.id = sm.product_id
            LEFT JOIN res_partner partner ON pick.partner_id = partner.id
            LEFT JOIN hr_employee emp ON emp.id = pick.delivery_driver_id
            WHERE 1=1
            AND pick.validate_date IS NOT NULL
            AND pick.delivery_driver_id IS NOT NULL
            AND (pick.delivery_state IN ({state_placeholders}))
            AND pick.division = %s
            AND emp.user_id = {uid}
            {type_condition}
            {search_condition}
            GROUP BY
                pick.id,
                pick.name,
                pick.origin,
                pick.validate_date,
                branch.name,
                partner.name,
                pick.delivery_state,
                emp.name
            ORDER BY
                CASE
                    WHEN pick.delivery_state = 'intransit' THEN 1
                    WHEN pick.delivery_state = 'draft' THEN 2
                    WHEN pick.delivery_state = 'delivered' THEN 3
                    ELSE 4
                END,
                pick.validate_date ASC
            LIMIT %s
            OFFSET %s
        """
        try:
            request._cr.execute(query, tuple(params))
            data = request._cr.dictfetchall()
            return valid_response(200, data if data else [])
        except Exception as e:
            message = f"Error in get_picking_transit: {str(e)}"
            _logger.error(message)
            return invalid_response(400, 'data_not_found', message, 'GET')
        
    @http.route('/api/expedition/<version>/get_travel_document', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_travel_document(self, **post):
        picking_id = int(post.get('picking_id'))
        if not picking_id:
            return invalid_response(400, 'Mandatory Parameter Not Found', 'Parameter picking_id tidak ada.')
        
        picking_obj = request.env['stock.picking'].suspend_security().browse(picking_id)
        if not picking_obj:
            return invalid_response(400, 'Picking Not Found', 'Picking tidak ditemukan.')

        try:
            url = str(request.httprequest.url).split('/api/')[0]
            filename = 'print_travel_document_' + str(picking_obj.id) + '.pdf'
            if not picking_obj.filename_upload_travel_document or not picking_obj.file_travel_document_show:
                get_file_travel_document = picking_obj.suspend_security()._get_file_travel_document()
                picking_obj.suspend_security().write({
                    'file_travel_document': get_file_travel_document,
                    'filename_upload_travel_document': filename,
                })
            data = {
                'file': url + '/web/content/stock.picking/' + str(picking_id) + '/file_travel_document_show',
                'filename': filename,
            }
            return valid_response(200, data)
        except Exception as e:
            messsage = f"Error in get_travel_document: {str(e)}"
            _logger.error(messsage)
            return invalid_response(400, 'data_not_found', messsage, 'GET')
