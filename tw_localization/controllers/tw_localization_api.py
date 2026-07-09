#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import logging
_logger = logging.getLogger(__name__)
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib
from odoo.addons.rest_api.rest_exception import invalid_response
from odoo.addons.rest_api.controllers.main import check_valid_token, valid_response
# 3:  imports of odoo
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
# 5: local imports

# 6: Import of unknown third party lib
class ControllerREST(http.Controller):
    @http.route('/api/master/<version>/get_country_state', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_country_state(self,version,**post):
        LIMIT = int(post.get('limit', 10))
        OFFSET = int(post.get('offset', 0))
        WHERE = "WHERE 1=1"
        ORDER = "ORDER BY sequence"
        if post.get('string'):
            WHERE += f" AND ((cs.code ilike '%%{post.get('string')}%%') or (cs.name ilike '%%{post.get('string')}%%'))"

        query = f"""
            SELECT cs.id
                , cs.name
                , cs.code
            FROM res_country_state cs
            INNER JOIN res_country c ON c.id = cs.country_id
            {WHERE}
            {ORDER}
            LIMIT {LIMIT}
            OFFSET {OFFSET}
        """
        request._cr.execute(query)
        ress =  request._cr.dictfetchall()

        return valid_response(200,ress)

    @http.route('/api/master/<version>/get_city', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_city(self,version,**post):
        LIMIT = int(post.get('limit', 10))
        OFFSET = int(post.get('offset', 0))
        WHERE = "WHERE 1=1"
        ORDER = "ORDER BY sequence"
        state_id = post.get('state_id',False)
        
        if state_id:
            WHERE += f" AND state_id = {int(state_id)}"

        if post.get('string'):
            WHERE += f" AND ((code ilike '%%{post.get('string')}%%') or (name ilike '%%{post.get('string')}%%'))" 

        query = f"""
            SELECT id
                , name
                , code
            FROM res_city
            {WHERE}
            {ORDER}
            LIMIT {LIMIT}
            OFFSET {OFFSET}
        """
        request._cr.execute (query)
        ress =  request._cr.dictfetchall()

        return valid_response(200,ress) 
    
    @http.route('/api/master/<version>/get_district', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_district(self,version,**post):
        LIMIT = int(post.get('limit', 10))
        OFFSET = int(post.get('offset', 0))
        WHERE = "WHERE 1=1"
        ORDER = "ORDER BY sequence"
        city_id = post.get('city_id',False)

        if city_id:
            WHERE += f" AND city_id = {int(city_id)}"
        
        if post.get('string'):
            WHERE += f" AND ((code ilike '%%{post.get('string')}%%') or (name ilike '%%{post.get('string')}%%'))" 
        
        query = f"""
            SELECT id
                , name
                , code
            FROM res_district
            {WHERE}
            {ORDER}
            LIMIT {LIMIT}
            OFFSET {OFFSET}
        """
        request._cr.execute(query)
        ress =  request._cr.dictfetchall()

        return valid_response(200,ress)
    
    @http.route('/api/master/<version>/get_sub_district', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_sub_district(self,version,**post):
        district_id = post.get('district_id',False)
        LIMIT = int(post.get('limit', 10))
        OFFSET = int(post.get('offset', 0))
        WHERE = "WHERE 1=1"
        ORDER = "ORDER BY sequence"

        if district_id:
            WHERE += f" AND district_id = {int(district_id)}"

        if post.get('string'):
            WHERE += f" AND ((code ilike '%%{post.get('string')}%%') or (name ilike '%%{post.get('string')}%%'))" 

        query = f"""
            SELECT id
                , name
                , code
                , zip_code
            FROM res_sub_district
            {WHERE}
            {ORDER}
            LIMIT {LIMIT}
            OFFSET {OFFSET}
        """
        request._cr.execute(query)
        ress =  request._cr.dictfetchall()
        
        return valid_response(200,ress)