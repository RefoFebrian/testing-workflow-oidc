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
    @http.route('/api/activity_atl_btl/<version>/get_act_line', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def act_line(self, version, **post):
        act_type_where = ''
        uid = request.session.uid
        
        if post.get('company_id'):
            company_id = int(post['company_id'])

        elif post.get('employee_id'):
            employee = request.env['hr.employee'].sudo().browse(int(post['employee_id']))
            employee_id = employee.id
            company_id = employee.company_id.id

        else:
            employee_id = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1).id
            company_id = False
            company_ids = request.env.user.company_ids
            if company_ids:
                company_id = company_ids[0].id
        
        if post.get('activity_type_id'):
            activity_type = post.get('activity_type')
            act_type_where += " AND act_type.id = '%s'" %activity_type
        if not company_id:
            return invalid_response(400, 'Company Not Found', 'Data Company Pada User Tidak Ditemukan!')

        limit = post.get('limit', 10)
        offset = post.get('offset', 0)

        if limit:
            act_type_where += f" LIMIT {limit}"
        if offset:
            act_type_where += f" OFFSET {offset}"
       
        month = date.today().month
        year = date.today().year
        query = """
                SELECT 
                prl.id as id,
                '[' || act_type.code || '] ' || COALESCE(prl.activity_name ,titik.name) as keramaian
                FROM tw_activity_atl_btl pr
                LEFT JOIN tw_activity_atl_btl_line prl ON prl.activity_id = pr.id
                LEFT JOIN tw_mapping_titik_keramaian mapping on mapping.id = prl.mapping_activity_id
                LEFT JOIN tw_master_activity_type as act_type on act_type.id = prl.act_type_id
                LEFT JOIN tw_titik_keramaian as titik on titik.id=mapping.activity_point_id
                WHERE 1=1
                AND pr.state != 'draft' 
                AND prl.state = 'confirmed'
                AND pr.company_id = %s 
                AND pr.month = '%s'  
                AND pr.year = '%s'
                %s
            """ %(company_id,month,year,act_type_where)
        
        request._cr.execute (query)
        ress =  request._cr.dictfetchall()
        
        return valid_response(200,ress)

    @http.route('/api/master/<version>/get_act_type', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def act_type(self, version, **post):
        uid = request.session.uid
        act_type = request.env['tw.master.activity.type'].sudo().search([('id','!=',0),('is_location','=',True)])

        data = []
        for act in act_type:
            data.append({
                'id':act.id,
                'name':act.name,
                'is_activity':act.is_btl    
            })
        
        return valid_response(200,data)