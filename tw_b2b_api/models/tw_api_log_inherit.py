#-*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import json
try:
    import simplejson as json
except ImportError:
    import json

from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib
from odoo.addons.rest_api.controllers.main import *
from odoo.addons.tw_b2b_api.controllers.main import check_ahm_ev_valid_token,invalid_response_json,valid_response_json,start_end_date_request

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

# 5: local imports

# 6: Import of unknown third party lib
import logging
_logger = logging.getLogger(__name__)

class TWEvApiLogInherit(models.Model):
    _inherit = "tw.api.log"

    def valid_post_response(self, name=None, url=None, request_time=None, request_type=None, request=None, type=None, response_time=None, response_code=200, jml_data=None, response=None):
        self.create({
            'name': name,
            'url': url,
            'request_time': request_time,
            'response_time': response_time,
            'response_code': str(response_code),
            'request': request,
            'response': response,
            # 'request_type': request_type,
            # 'type': type,
            # 'jml_data': jml_data,
        })

    def invalid_post_response(self, name=None, url=None, request_time=None, request_type=None, request=None, type=None, response_time=None, response_code=400, jml_data=None, response=None):
        self.create({
            'name': name,
            'url': url,
            'request_time': request_time,
            'response_time': response_time,
            'response_code': str(response_code),
            'request': request,
            'response': response,
            # 'request_type': request_type,
            # 'type': type,
            # 'jml_data': jml_data,
        })