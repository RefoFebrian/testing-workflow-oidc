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
from odoo.addons.rest_api.rest_exception import invalid_response
from odoo.addons.rest_api.controllers.main import check_valid_token, valid_response
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
    @http.route('/api/master/<version>/branch', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def branch(self,version,**post):
        uid = request.session.uid
        company_id = False
        company_ids = request.env.user.company_ids
        if company_ids:
            company_id = str(tuple(company_ids.ids)).replace(',)', ')')

        if not company_id:
            error = 'Branch Not Found'
            info = 'Data Branch Tidak Ditemukan!'
            return invalid_response(400, error,info)
        
        WHERE = "WHERE branch.id in %s" %company_id
        string = False
        if 'string' in post:
            string = post['string']
            WHERE += " AND ((branch.name ilike '%%%s%%') or (branch.code ilike '%%%s%%'))" %(string,string) 

        limit = 10
        offset = 0

        if 'limit' in post:
            limit = int(post['limit'])

        if 'offset' in post:
            offset = int(post['offset'])

        branch = """
            SELECT branch.id
                , '[' || branch.code || '] ' || branch.name as name
            FROM res_company as branch
            %s
            LIMIT %d OFFSET %d
        """ %(WHERE, limit, offset)
        request._cr.execute (branch)
        ress =  request._cr.dictfetchall()

        return valid_response(200,ress)