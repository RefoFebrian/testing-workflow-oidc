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
    @http.route('/api/employee/<version>/profile', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def profile(self,**post):
        uid = request.session.uid
        query = """
            SELECT
                u.id as id
                , hr.name as name
                , j.name->>'en_US' as role
                , p.id as partner_id
                , hr.atpm_id as honda_id 
                , '' as tunas_id
                , hr.work_email as email
                , hr.birthday::varchar as tgl_lahir
                , hr.gender as gender
                , hr.working_start_date::varchar as tgl_join
                , '' as url_image_profile
            FROM hr_employee hr
            INNER JOIN resource_resource r ON r.id = hr.resource_id 
            INNER JOIN res_users u ON u.id = r.user_id
            INNER JOIN res_partner p ON p.id = u.partner_id
            INNER JOIN hr_job j ON j.id = hr.job_id
            WHERE u.id = %d
        """ %(uid)
        request._cr.execute (query)
        ress =  request._cr.dictfetchone()

        return valid_response(200,ress)

    @http.route('/api/master/<version>/salesman', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def salesman(self,version,**post):
        uid = request.session.uid
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        company_id = False
        company_ids = request.env.user.company_ids
        if company_ids:
            company_id = str(tuple([b.id for b in company_ids])).replace(',)', ')')

        if not company_id:
            error = 'Branch Not Found'
            info = 'Data Branch Tidak Ditemukan!'
            return invalid_response(400, error,info)
        
        limit = 10
        offset = 0

        if 'limit' in post:
            limit = int(post['limit'])

        if 'offset' in post:
            offset = int(post['offset'])
        
        WHERE = " WHERE 1=1 AND he.atpm_id is not null AND he.working_end_date is null" 
        
        if post.get('id'):
            WHERE += f" AND he.company_id = {int(post['id'])}"
        else:
            WHERE += f" AND he.company_id in {company_id}"

        if 'Sales Digital' in (employee_id.job_id.name or ''):
            WHERE = " WHERE 1=1 AND he.atpm_id is not null AND he.working_end_date is null" 
            WHERE += ' AND ('
            if post.get('id'):
                WHERE += f" he.company_id = {int(post.get('id'))}"
                WHERE += " OR "

            WHERE += "hj.name ilike '%%Sales Digital' )" 

        if post.get('name'):
            WHERE += f" AND ((he.name ilike '%%{post.get('name')}%%') or (atpm_id ilike '%%{post.get('name')}%%'))" 
        if post.get('job_name'):
            WHERE += f" AND hj.name ilike '%%{post.get('job_name')}%%'"
        
        if post.get('string'):
            WHERE += f" AND ((he.name ilike '%%{post.get('string')}%%') or (atpm_id ilike '%%{post.get('string')}%%'))" 

        employee = f"""
            SELECT he.id
                , '[' || he.atpm_id || '] ' || he.name as name
            FROM hr_employee he
            LEFT JOIN hr_job hj ON hj.id = he.job_id
            {WHERE}
            LIMIT {limit} OFFSET {offset}
        """
        request._cr.execute(employee)
        ress =  request._cr.dictfetchall()

        return valid_response(200,ress)