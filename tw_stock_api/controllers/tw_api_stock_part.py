# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

try:
    import simplejson as json
except ImportError:
    import json

from datetime import datetime

# 2: imports of odoo
from odoo import http
from odoo.http import request

# 3: imports from odoo modules
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response 
from odoo.addons.rest_api.controllers.main import check_valid_token

_logger = logging.getLogger(__name__)

class ControllerREST(http.Controller):
    @http.route('/api/enginereport/stock_md_part', methods=['GET'], type='http', auth='none', csrf=False)
    def stock_md_part(self, **post):
        api_log = request.env['tw.api.log']
        url = '/api/enginereport/stock_md_part'
        name = 'Get Stock MD Part'
        request_time = datetime.now()

        try:
            product_code = post.get('product_code', None)

            data = self._get_stock_part_md(product_code)
            response_time = datetime.now()
            api_log.sudo().create_api_log(
                name=name,
                url=url,
                description=None,
                ip_address=None,
                response=None,
                payload=post,
                header=None,
                response_code='200',
                status_code='success')
            return valid_response(200, data)

        except Exception as e:
            response_time = datetime.now()
            _logger.error(f'Error in stock_md_part: {e}')
            api_log.sudo().create_api_log(
                name=name,
                url=url,
                description=None,
                ip_address=None,
                payload=post,
                header=None,
                response_code='500',
                status_code='error',
                response=str(e))
            return invalid_response(400, 'Error Exception', str(e))
    
    def _get_stock_part_md(self, **kwargs):
        product_code = kwargs.get('product_code', None)
        
        query_where = ''
        if product_code:
            query_where += f"AND pt.default_code IN {product_code}"
            
        query = """
            SELECT
                sl.company_id AS branch_id
                , sq.product_id AS product_id
                , rc.code AS branch_code
                , pt.default_code AS product_code
                , pt."name"->>'en_US' AS description
                , sum(sq.quantity) AS total
            FROM stock_quant sq
            LEFT JOIN stock_location sl ON sl.id = sq.location_id
            LEFT JOIN res_company rc ON rc.id = sl.company_id
            LEFT JOIN stock_lot sl2 ON sl2.id = sq.lot_id
            LEFT JOIN product_product pp ON pp.id = sq.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN product_category pc ON pc.id = pt.categ_id
            WHERE 1=1
            AND pc.id IN (
                SELECT
                    coalesce(pc3.id,coalesce(pc2.id,coalesce(pc1.id,null))) AS id_layer_3
                FROM product_category pc1
                left join product_category pc2 on pc2.parent_id = pc1.id
                left join product_category pc3 on pc3.parent_id = pc2.id
                where pc1.name = 'Sparepart'
            )
            AND sl."usage" = 'internal'
            AND rc.code = 'MML'
            {query_where}
            GROUP BY sl.company_id, sq.product_id, rc.code, pt.default_code, pt.name->>'en_US'
        """.format(query_where=query_where)

        request.env.cr.execute(query)
        ress = request.env.cr.dictfetchall()
        list_of_dict_stock_master = []

        if ress:
            for res in ress:
                dict_of_stock_master = {}
                total = res['total']
                qty_picking = self._get_qty_picking(res['branch_id'], 'Sparepart', res['product_id'])
                stock_avb = total - qty_picking

                dict_of_stock_master.update({
                    'product_id': res['product_id'],
                    'branch_code': res['branch_code'],
                    'product_code': res['product_code'],
                    'description': res['description'],
                    'total': total,
                    'total_picking': qty_picking,
                    'stock_avb': stock_avb
                })

                list_of_dict_stock_master.append(dict_of_stock_master)
        
        return list_of_dict_stock_master

    def _get_qty_picking(self, company_id, division, product_id):
        qty_picking_product = 0
        obj_picking = request.env['stock.picking'].sudo()
        obj_move = request.env['stock.move'].sudo()

        picking_type_ids = request.env['stock.picking.type'].sudo().search([
            ('company_id', '=', company_id),
            ('code', 'in', ['outgoing', 'interbranch_out'])])

        if picking_type_ids:
            picking_ids = obj_picking.sudo().search([
                ('company_id', '=', company_id),
                ('division', '=', division),
                ('picking_type_id', 'in', picking_type_ids.ids),
                ('state', 'not in', ['draft', 'cancel', 'done'])])

            if picking_ids:
                move_ids = obj_move.sudo().search([
                    ('picking_id', 'in', picking_ids.ids),
                    ('product_id', '=', product_id)])
                
                if move_ids:
                    for move in move_ids:
                        qty_picking_product += move.product_uom_qty
        
        return qty_picking_product
        
