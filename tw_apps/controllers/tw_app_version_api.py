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
try:
    from packaging import version as parse_version
except ImportError:
    from odoo.tools import parse_version as parse_version

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

class controllerREST(http.Controller):
    @http.route('/api/app/<version_api>/version_check', methods=['POST'], type='http', auth='none', csrf=False)
    def app_version_check(self, version_api, **post):
        app = post['app_name']
        app_version = post['version_name']
        obj_version=request.env['tw.app.version'].sudo().search([('app_type_id.active','=',True),('app_type_id.value','=',app.lower())])
        if not obj_version:
            info = "Konfigurasi APK version untuk %s belum tersedia. "%(post['app_name'] )
            error = "Config not Found"
            return invalid_response(400, error,info)
        

        ver=[]
        if obj_version :
            for ve in obj_version :
                ver.append(str(ve.name))
                
        if post['version_name'] not in  ver :
            info = "Versi APK %s Harus %s , Versi APK %s Anda Saat ini %s "%(app,ver,app,post['version_name'] )
            error = "Wrong Version"
            status_code = 500
            
            if parse_version(app_version) > parse_version('10.1'):
                status_code = 428
            return invalid_response(status_code, error,info)
        
        data = {
            'message':'ok',
        }
        
        return valid_response(200,data)