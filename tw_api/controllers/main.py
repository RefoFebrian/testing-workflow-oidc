# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import functools
import logging

import json
import datetime

import werkzeug.urls
import werkzeug.utils
from werkzeug.exceptions import BadRequest
from odoo.http import Response
from odoo import api, http, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo import registry as registry_get
import jwt
from jwt.algorithms import RSAAlgorithm

from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home


_logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        return json.JSONEncoder.default(self, obj)

class DateTimeEncoder(JSONEncoder):
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

def valid_response(status, data, message='Success'):
    response = {
        'status': 1,
        'message': message,
        'code': status,
        'data': data
    }
    
    if request.httprequest.content_type == 'application/json':
        werkzeug.wrappers.Response.status_code = 200
        return response

    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(response, cls=JSONEncoder),
    )

def invalid_response(status, error, info, version=None):
    if 'opt' in str(info) or 'syntax' in str(info):
        info = 'Error !, Please contact administrator if you think this is a mistake.'
    response = {
        'status': 0,
        'message': 'Failed',
        'code': status,
        'data': {
            'error': error,
            'error_descrip': info,
        }
    }

    if request.httprequest.content_type == 'application/json':
        werkzeug.wrappers.Response.statu_code = status
        return response

    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(response)
    )

def check_sensitive_value(convert_type,value):
    try:
        value = convert_type(value)
    except:
        return False
    return value