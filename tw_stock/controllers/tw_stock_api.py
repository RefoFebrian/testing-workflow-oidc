#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import functools
import werkzeug.wrappers
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response 
from odoo.addons.rest_api.controllers.main import check_valid_token
# 3:  imports of odoo
import odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class ControllerREST(http.Controller):
    @http.route('/api/stock/<version>/get_sales_source_location', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_sales_source_location(self, version, **post):
        uid = request.session.uid
        query_where = ""
        if post.get('employee_id'):
            employee = request.env['hr.employee'].sudo().browse(int(post['employee_id']))
            employee_id = employee.id
            company_id = employee.company_id.id
            # company_id = int(post['company_id']) if post.get('company_id') else employee.company_id.id
        else:
            employee_id = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1).id
            company_id = False
            company_ids = request.env.user.company_ids
            if company_ids:
                company_id = company_ids[0].id
            if post.get('company_id'):
                company_id = int(post['company_id'])
        if not company_id:
            return invalid_response(400, 'Branch Not Found', 'Data Branch Pada User Tidak Ditemukan!')

        limit = post.get('limit', 10)
        offset = post.get('offset', 0)

        if limit:
            query_where += f" LIMIT {limit}"
        if offset:
            query_where += f" OFFSET {offset}"
        
        query = f"""
               SELECT
                a.id,
                a.complete_name as name
                FROM stock_location as a
                WHERE a.active IS TRUE
                AND a.usage='internal'
                AND a.company_id={company_id}
                {query_where}
            """ 
        request._cr.execute(query)
        ress =  request._cr.dictfetchall()
        
        return valid_response(200,ress)
