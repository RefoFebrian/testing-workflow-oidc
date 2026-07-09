# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

try:
    import simplejson as json
except ImportError:
    import json

from datetime import datetime
import calendar

# 2: imports of odoo
from odoo import http
from odoo.http import request

# 3: imports from odoo modules
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response
from odoo.addons.rest_api.controllers.main import check_valid_token

_logger = logging.getLogger(__name__)


class ControllerREST(http.Controller):
    @http.route('/api/enginereport/picking_file_distribution', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def picking_file_distribution(self, **post):
        api_log = request.env['tw.api.log']
        url = '/api/enginereport/picking_file_distribution'
        name = 'Get Picking File Distribusi'
        request_time = datetime.now()

        today = datetime.now().date()
        last_day_of_month = calendar.monthrange(today.year, today.month)
        try:
            date_start = datetime.strptime(post.get('date_start'), '%Y-%m-%d').replace(day=1).strftime('%Y-%m-%d')
            date_end = post.get('date_end', today.replace(day=last_day_of_month[1]).strftime('%Y-%m-%d'))
            product_code = post.get('product_code', False)
            
            query_picking = self._api_stock_picking(date_start=date_start, date_end=date_end)
            query_master_stock = self._api_master_stock(product_code=product_code)
            data = {
                'query_data_file_distribution': query_picking,
                'query_data_master_stock': query_master_stock
            }
            
            response_time = datetime.now()
            api_log.sudo().create_api_log(
                name=name,
                url=url,
                description=None,
                ip_address=None,
                response=None,
                payload=post,
                header=None,
                response_code=200,
                status_code='success')
            return valid_response(200, data)
        except ValueError as e:
            api_log.sudo().create_api_log(
                name=name,
                url=url,
                description=None,
                ip_address=None,
                payload=post,
                header=None,
                response_code=400,
                status_code='error',
                response=str(e))
            return invalid_response(400, 'Error Exception', str(e))
        
    def _api_stock_picking(self, **kwargs):
        result = ''
        picking_type_obj = request.env['stock.picking.type'].sudo()
        picking_types = picking_type_obj.search([('code', 'in', ['outgoing'])])
        main_dealer = request.env['res.company'].sudo().search([('code', '=', 'MML')], limit=1)
        
        start_date = False
        end_date = False

        if kwargs.get('date_start'):
            start_date = kwargs.get('date_start')

        if kwargs.get('date_end'):
            end_date = kwargs.get('date_end')

        picking_obj = request.env['stock.picking'].sudo().search([
            ('picking_type_id', 'in', picking_types.ids),
            ('division', '=', 'Unit'),
            ('company_id', '=', main_dealer.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('state', 'not in', ('draft', 'cancel'))
        ])

        for picking in picking_obj:
            partner_id = False
            if picking.mutation_order_id:
                mutation_order = picking.mutation_order_id
                partner_id = mutation_order.requester_id
            else:
                partner_id = picking.partner_id

            for move in picking.move_ids:
                dealer_code = False
                if partner_id.category_id.name == 'Dealer':
                    dealer_code = partner_id.code

                date = move.date
                month = date.month
                year = date.year
                day = date.day
                new_date = '%s-%s-%s' % (day, month, year)
                result += str(picking.origin) + ';' + str(move.product_id.name) + ';' + str(move.product_id.description) + ';' + str(move.product_id.product_template_attribute_value_ids.code) + ';' + str(move.product_qty) + ';' + str(new_date) + ';' + str(picking.name) + ';' + str(dealer_code) + ';' + str(partner_id.name)
                result += '\n'

        return result

    def _api_master_stock(self, product_code=None):
        query_where = ""

        if product_code:
            query_where += f" AND pp.name_template = '{product_code}'"
            
        query = """
            SELECT
                sl.company_id AS branch_id
                , sq.product_id as product_id
                , rc.name as branch_name
                , rc.code as branch_code
                , pp.default_code as product_code
                , pav.code as color
                , pt.name->>'en_US' as description
                , sum(sq.quantity) as total
                , COALESCE((
                    SELECT SUM(product_uom_qty)
                        FROM stock_move sm
                        LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
                        LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                            WHERE spt.code IN ('outgoing','internal')
                            AND sp.company_id = rc.id
                            AND sp.state not IN ('draft','cancel','done')
                            AND sp.division = 'Unit'
                            AND sm.product_id = pp.id),0) as total_picking
                , sum(sq.quantity) - COALESCE((
                    SELECT SUM(product_uom_qty)
                        FROM stock_move sm
                        LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
                        LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                            WHERE spt.code IN ('outgoing','internal')
                            AND sp.company_id = rc.id
                            AND sp.state not IN ('draft','cancel','done')
                            AND sp.division = 'Unit'
                            AND sm.product_id = pp.id),0) as stock_avb
            FROM stock_quant sq
            LEFT JOIN stock_location sl ON sl.id = sq.location_id
            LEFT JOIN res_company rc ON rc.id = sl.company_id
            LEFT JOIN stock_lot sl2 ON sl2.id = sq.lot_id
            LEFT JOIN product_product pp ON pp.id = sl2.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN product_variant_combination as pvc on pvc.product_product_id = pp.id
            LEFT JOIN product_template_attribute_value as ptav on ptav.id = pvc.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            LEFT JOIN product_category pc ON pc.id = pt.categ_id
            WHERE sl.usage='internal'
            AND sl2.ready_for_sale = 'good'
            AND pc.id IN (
                SELECT
                    coalesce(pc3.id,coalesce(pc2.id,coalesce(pc1.id,null))) AS id_layer_3
                FROM product_category pc1
                left join product_category pc2 on pc2.parent_id = pc1.id
                left join product_category pc3 on pc3.parent_id = pc2.id
                where pc1.name = 'Unit'
            )
            AND rc.code = 'MML'
            {query_where}
            GROUP BY sl.company_id, sq.product_id, rc.id, pp.id, pav.code, pt.name->>'en_US'
            ORDER by branch_name, branch_code, product_code, color
        """.format(query_where=query_where)

        request._cr.execute(query)
        ress = request._cr.dictfetchall()

        return ress
        
                
