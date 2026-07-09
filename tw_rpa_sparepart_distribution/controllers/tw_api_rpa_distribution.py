# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

try:
    import simplejson as json
except ImportError:
    import json

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 2: imports of odoo
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError as Warning

# 3: imports from odoo modules
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response 
from odoo.addons.rest_api.controllers.main import check_valid_token

_logger = logging.getLogger(__name__)

class ControllerREST(http.Controller):
    @http.route('/api/rpa/mktbb/stock_md', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_distribusi_sparepart(self, **post):
        api_log = request.env['tw.api.log']
        url = '/api/rpa/mktbb/stock_md'
        name = 'RPA Stock MD'
        request_time = datetime.now()

        try:
            data, result = self._get_stock_md(date=post.get('date'), interval=post.get('interval'))
            
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
            return valid_response(200, data, result)

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
                response_code=400,
                status_code='error',
                response=str(e))
            return invalid_response(400, 'Error Exception', str(e))

    @http.route('/api/rpa/mktbb/distrib_dealer', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_distribusi_dealer(self, **post):
        api_log = request.env['tw.api.log']
        url = '/api/rpa/mktbb/distrib_dealer'
        name = 'RPA Distrib Dealer'
        request_time = datetime.now()

        try:
            data, result = self._get_distribusi_dealer(
                date_day=post.get('date_day', None),
                dealer_only=post.get('dealer_only', False),
                file_existed=post.get('file_existed', None)
            )
            
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
            return valid_response(200, data, result)

        except Exception as e:
            response_time = datetime.now()
            _logger.error(f'Error in distrib_dealer_part: {e}')
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
    
    def _get_stock_md(self, date=None, interval=None):
        parent_categ = request.env['product.category'].sudo().search([('name', '=', 'Unit')])
        categ_ids = request.env['product.category'].sudo().search([('id', 'child_of', parent_categ.id)]).ids
        
        query_date = ""
        if date and interval:
            date = datetime.strptime(date, '%Y-%m-%d')
            query_date = " AND (sq.in_date + INTERVAL '7 HOURS')::DATE <= '{date}'".format(
                date=(date - relativedelta(days=int(interval))).strftime('%Y-%m-%d')
            )

        query = """
            SELECT
                pc2."name" AS segment
                , rc.id AS bid
                , pp.id AS pid
                , SUM(sq.quantity) AS qty
            FROM stock_quant sq
            LEFT JOIN stock_location sl ON sl.id = sq.location_id
            LEFT JOIN res_company rc ON rc.id = sl.company_id
            LEFT JOIN stock_lot sl2 ON sl2.id = sq.lot_id
            LEFT JOIN product_product pp ON pp.id = sq.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN product_category pc ON pc.id = pt.categ_id
            LEFT JOIN product_category pc2 ON pc2.id = pc.parent_id
            WHERE 1=1
            AND sl.usage='internal'
            AND sl2.ready_for_sale='good'
            AND rc.code = 'MML'
            AND pc.id IN {categ_ids}
            {query_date}
            GROUP BY pc2.name, rc.id, pp.id, sq.quantity
        """.format(
                categ_ids=str(tuple(categ_ids)).replace(',)', ')'),
                query_date=query_date)

        request.env.cr.execute(query)
        stock_res = request.env.cr.dictfetchall()
        if not stock_res:
            error = 'Tidak ada data stok!'
            _logger.error(error)
            raise Warning(error)
            return invalid_response(404, 'Data Not Found', error)

        stocks = {
            'CUB': 0,
            'AT': 0,
            'SPORT': 0,
        }
        
        try:
            for stock in stock_res:
                picking_qty = request.env['stock.picking'].sudo()._get_qty_picking(stock['bid'], 'Unit', stock['pid'])
                final_qty = stock['qty'] - picking_qty
                if stock['segment'] in stocks.keys():
                    stocks[stock['segment']] += final_qty
                else:
                    stocks[stock['segment']] = final_qty
        except Exception as e:
            error = 'Gagal mendapatkan data Stok.\n\nDetail:\n%s: %s' % (type(e), e)
            _logger.error(error)
            raise Warning(error)
            return invalid_response(500, 'Internal Server Error', error)

        result = 'Stock data fetched!'
        return stocks, result

    def _get_distribusi_dealer(self, date_day=None, dealer_only=False, file_existed=None):
        gc_user_ids = request.env['ir.config_parameter'].sudo().get_param('tw_rpa_sparepart_distribution.gc_user_ids')
        selected_columns = """
             --  1. Total this Month
            SUM(data.qty) FILTER (
                WHERE EXTRACT (DAY FROM data.date) = series.date
                AND EXTRACT (MONTH FROM data.date) = EXTRACT (MONTH FROM now())
                AND EXTRACT (YEAR FROM data.date) = EXTRACT (YEAR FROM now())
            ),
            --  2. Total last Month
            SUM(data.qty) FILTER (
                WHERE EXTRACT (DAY FROM data.date) = series.date
                AND EXTRACT (MONTH FROM data.date) = EXTRACT (MONTH FROM now() - INTERVAL '1 MONTHS')
                AND EXTRACT (YEAR FROM data.date) = EXTRACT (YEAR FROM now() - INTERVAL '1 MONTHS')
            ),
            --  3. This Month (Cabang only)
            SUM(data.qty) FILTER (
                WHERE data.type = 'outgoing' AND data.is_mutation_order IS TRUE
                AND EXTRACT (DAY FROM data.date) = series.date
                AND EXTRACT (MONTH FROM data.date) = EXTRACT (MONTH FROM now())
                AND EXTRACT (YEAR FROM data.date) = EXTRACT (YEAR FROM now())
            ),
            --  4. Last Month (Cabang only)
            SUM(data.qty) FILTER (
                WHERE data.type = 'outgoing' AND data.is_mutation_order IS TRUE
                AND EXTRACT (DAY FROM data.date) = series.date
                AND EXTRACT (MONTH FROM data.date) = EXTRACT (MONTH FROM now() - INTERVAL '1 MONTHS')
                AND EXTRACT (YEAR FROM data.date) = EXTRACT (YEAR FROM now() - INTERVAL '1 MONTHS')
            ),
            --  5. This Month (Dealer only)
            SUM(data.qty) FILTER (
                WHERE data.type = 'outgoing'
                AND EXTRACT (DAY FROM data.date) = series.date
                AND EXTRACT (MONTH FROM data.date) = EXTRACT (MONTH FROM now())
                AND EXTRACT (YEAR FROM data.date) = EXTRACT (YEAR FROM now())
            ),
            --  6. Last Month (Dealer only)
            SUM(data.qty) FILTER (
                WHERE data.type = 'outgoing'
                AND EXTRACT (DAY FROM data.date) = series.date
                AND EXTRACT (MONTH FROM data.date) = EXTRACT (MONTH FROM now() - INTERVAL '1 MONTHS')
                AND EXTRACT (YEAR FROM data.date) = EXTRACT (YEAR FROM now() - INTERVAL '1 MONTHS')
            ),
            --  7. This Month (Cabang DMP & DLR only)
            SUM(data.qty) FILTER (
                WHERE data.type = 'outgoing' AND data.is_mutation_order IS TRUE
                AND EXTRACT (DAY FROM data.date) = series.date
                AND EXTRACT (MONTH FROM data.date) = EXTRACT (MONTH FROM now())
                AND EXTRACT (YEAR FROM data.date) = EXTRACT (YEAR FROM now())
                AND data.dealer_code IN ('TDM-DLR','DMP','A0005')
            ),
            --  8. Last Month (Cabang DMP & DLR only)
            SUM(data.qty) FILTER (
                WHERE data.type = 'outgoing' AND data.is_mutation_order IS TRUE
                AND EXTRACT (DAY FROM data.date) = series.date
                AND EXTRACT (MONTH FROM data.date) = EXTRACT (MONTH FROM now() - INTERVAL '1 MONTHS')
                AND EXTRACT (YEAR FROM data.date) = EXTRACT (YEAR FROM now() - INTERVAL '1 MONTHS')
                AND data.dealer_code IN ('TDM-DLR','DMP','A0005')
            )
        """

        if dealer_only:
            selected_columns = """
                --  5. This Month (Dealer only)
                SUM(data.qty) FILTER (
                    WHERE data.type = 'outgoing'
                    AND EXTRACT (DAY FROM data.date) = series.date
                    AND EXTRACT (MONTH FROM data.date) = EXTRACT (MONTH FROM now())
                    AND EXTRACT (YEAR FROM data.date) = EXTRACT (YEAR FROM now())
                ),
                --  6. Last Month (Dealer only)
                SUM(data.qty) FILTER (
                    WHERE data.type = 'outgoing'
                    AND EXTRACT (DAY FROM data.date) = series.date
                    AND EXTRACT (MONTH FROM data.date) = EXTRACT (MONTH FROM now() - INTERVAL '1 MONTHS')
                    AND EXTRACT (YEAR FROM data.date) = EXTRACT (YEAR FROM now() - INTERVAL '1 MONTHS')
                )
            """

        distribution_query = """
            SELECT series.date,(
                SELECT ( {selected_columns} )
                FROM (
                    SELECT
                        sm.product_qty AS qty
                        , (sp.date + INTERVAL '7 HOURS') AS date
                        , sp.create_uid AS pick_uid
                        , CASE
                            WHEN tmo.id IS NOT NULL THEN TRUE
                            ELSE FALSE
                        END AS is_mutation_order
                        , spt.code AS type
                        ,   CASE
                                WHEN tmo.id IS NOT NULL THEN rp3.code  -- came from mutation order
                                WHEN so.id IS NOT NULL THEN rp2.code  -- came from sale order
                                ELSE rp.code
                            END AS dealer_code
                        , state.code AS state_code
                    FROM stock_move sm
                    LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                    LEFT JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
                    LEFT JOIN res_company rc ON rc.id = sp.company_id
                    LEFT JOIN res_partner rp ON rp.id = sp.partner_id
                    -- Sale Order path
                    LEFT JOIN sale_order so ON so.id = sp.sale_id
                    LEFT JOIN res_partner rp2 ON rp2.id = so.partner_id
                    -- Mutation Order path
                    LEFT JOIN tw_mutation_order tmo ON tmo.id = sp.mutation_order_id
                    LEFT JOIN res_company rc2 ON rc2.id = tmo.requester_id
                    LEFT JOIN res_partner rp3 ON rp3.id = rc2.partner_id
                    LEFT JOIN res_city city ON city.id = rc2.city_id
                    LEFT JOIN res_country_state state ON state.id = city.state_id
                    WHERE spt.code IN ('outgoing','interbranch_out')
                    AND rc.code = 'MML'
                    AND sp.division = 'Unit'
                    AND sp.state NOT IN ('draft','cancel')
                ) AS data
                -- Exclude Non Lampung Distributions (currently only GC units)
                WHERE data.pick_uid NOT IN (
                    SELECT id FROM res_users WHERE login IN {gc_user_ids}
                )
            )
            FROM (
                SELECT date
                FROM generate_series (
                    {start_day},{end_day}
                ) date
            ) AS series
        """.format(
            selected_columns=selected_columns,
            start_day="EXTRACT(DAY FROM now())::INT" if file_existed else "1",
            end_day="EXTRACT(DAY FROM now())::INT" if not date_day else date_day,
            gc_user_ids=gc_user_ids
        )

        try:
            request.env.cr.execute(distribution_query)
            distribution_res = request.env.cr.dictfetchall()
            if not distribution_res:
                error = 'Tidak ada data distribusi!'
                _logger.error(error)
                raise Warning(error)
                return invalid_response(404, 'Data Not Found', error)
        except Exception as e:
            error = 'Gagal mendapatkan data Distribusi.\n\nDetail:\n%s: %s' % (type(e), e)
            _logger.error(error)
            raise Warning(error)
            return invalid_response(500, 'Internal Server Error', error)

        result = 'Distribution data fetched!'
        _logger.info(result)
        return distribution_res, result
        
        
