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
    @http.route('/api/master/<version>/fincoy', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def fincoy(self,version,**post):
        WHERE = " WHERE p.active is TRUE AND cat.name->>'en_US' = 'Finance Company'"
        LIMIT = 10
        OFFSET = 0

        if post.get('string'):
            WHERE += f" AND ((p.name ilike '%%%{post['string']}%%') or (p.code ilike '%%%{post['string']}%%'))" 

        if post.get('limit', False):
            LIMIT = int(post['limit'])
        if post.get('offset', False):
            OFFSET = int(post['offset'])
    
        query = f"""
            SELECT DISTINCT
                p.id,
                p.name
            FROM res_partner p
            JOIN res_partner_res_partner_category_rel rel ON p.id = rel.partner_id
            JOIN res_partner_category cat ON rel.category_id = cat.id
            {WHERE}
            LIMIT {LIMIT} OFFSET {OFFSET}
        """
        request._cr.execute (query)
        ress =  request._cr.dictfetchall()

        return valid_response(200,ress)

    @http.route('/api/master/<version>/get_customer_stnk', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_customer_stnk(self,version,**post):
        WHERE = " WHERE p.active is TRUE AND cat.name->>'en_US' = 'Customer'"
        LIMIT = 10
        OFFSET = 0

        if post.get('string'):
            WHERE += f" AND ((p.name ilike '%%%{post['string']}%%') or (p.code ilike '%%%{post['string']}%%'))" 

        if post.get('limit', False):
            LIMIT = int(post['limit'])
        if post.get('offset', False):
            OFFSET = int(post['offset'])
    
        query = f"""
            SELECT DISTINCT
                p.id,
                p.name
            FROM res_partner p
            JOIN res_partner_res_partner_category_rel rel ON p.id = rel.partner_id
            JOIN res_partner_category cat ON rel.category_id = cat.id
            {WHERE}
            LIMIT {LIMIT} OFFSET {OFFSET}
        """
        request._cr.execute(query)
        ress = request._cr.dictfetchall()

        return valid_response(200, ress)

    @http.route('/api/master/<version>/post_customer_stnk', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_customer_stnk(self, version, **post):
        uid = request.session.uid
        post = json.loads(request.httprequest.get_data(as_text=True))
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1)
        company_id = False
        company_ids = request.env.user.company_ids
        if company_ids and len(company_ids) == 1 :
            company_id = company_ids[0].id
        if not company_id:
            company_id = employee_id.company_id.id
        if not company_id:
            error = 'Branch ID'
            info = 'data_not_found'
            return invalid_response(400, error,info)
            
        # Required fields validation
        required_fields = [
            'nama',
            'no_ktp',
            'mobile',
            'address'
        ]
        
        missing_fields = [field for field in required_fields if field not in post]
        if missing_fields:
            error = f'Missing required fields: {", ".join(missing_fields)}'
            return invalid_response(400, error, 'missing_required_fields')

        src_customer = request.env['res.partner'].search([('identification_number','ilike',post['no_ktp'])],limit=1)
        if not src_customer:
            create = request.env['res.partner'].sudo().create({
                'identification_number': post['no_ktp'],
                'name':post['nama'],
                'mobile':post['mobile'],
                'company_id':company_id,
                'occupation_id':post['pekerjaan_id'],
                'street':post['address'],
                'state_id':post['state_id'],
                'city_id':post['kabupaten_id'],
                'district_id':post['kecamatan_id'],
                'sub_district_id':post['kelurahan_id'],
                'zip':post['kode_pos'],

            })
            if create:
                return valid_response(200,create.identification_number)
        else :
            src_customer.sudo().write({
                'identification_number': post['no_ktp'],
                'name':post['nama'],
                'mobile':post['mobile'],
                'company_id':company_id,
                'occupation_id':post['pekerjaan_id'],
                'street':post['address'],
                'state_id':post['state_id'],
                'city_id':post['kabupaten_id'],
                'district_id':post['kecamatan_id'],
                'sub_district_id':post['kelurahan_id'],
                'zip':post['kode_pos'],
            })
            return valid_response(200,src_customer.identification_number)

