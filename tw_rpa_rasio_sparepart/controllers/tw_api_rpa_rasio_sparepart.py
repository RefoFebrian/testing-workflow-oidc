# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

try:
    import simplejson as json
except ImportError:
    import json

from datetime import date, datetime

# 2: imports of odoo
from odoo import http
from odoo.http import request

# 3: imports from odoo modules
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response 
from odoo.addons.rest_api.controllers.main import check_valid_token

_logger = logging.getLogger(__name__)

class TwApiRpaRasioSparepart(http.Controller):
    @http.route('/api/teto/rpa_rasio_sparepart', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def rpa_rasio_sparepart(self, **post):
        api_log = request.env['tw.api.log']
        url = '/api/teto/rpa_rasio_sparepart'
        name = 'RPA Rasio Sparepart'

        try:
            query_penjualan_md = request.env['tw.main.dealer.sales.report'].sudo().create({
                'start_date': post.get('start_date') or date.today().strftime("%Y-%m-%d"),
                'end_date': post.get('end_date') or date.today().strftime("%Y-%m-%d"),
                'division': 'Sparepart',
                'product_ids': False,
                'state': 'all',
                'company_ids': False,
                'dealer_ids': False,
            }).with_context(api_rpa=True)._print_excel_report()
            request._cr.execute(query_penjualan_md)
            data_penj_md = request.env.cr.dictfetchall()

            query_mutation_detail = request.env['tw.mutation.detail.report'].sudo().create({
                'start_date': post.get('start_date') or date.today().strftime("%Y-%m-%d"),
                'end_date': post.get('end_date') or date.today().strftime("%Y-%m-%d"),
                'company_ids': False,
                'state': 'all'
            }).with_context(api_rpa=True, is_workshop=True).excel_report()
            request._cr.execute(query_mutation_detail)
            data_mutation_detail = request.env.cr.dictfetchall()

            result = {
                'penjualan_md': data_penj_md,
                'mutation_detail': data_mutation_detail,
            }

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
            return valid_response(200, result)
            
        except Exception as e:
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
            _logger.error(f"Error in rpa_rasio_sparepart: {str(e)}")
            return invalid_response(400, 'Internal Server Error', str(e))
