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

class TwEvApiConfigurationInherit(models.Model):
    _inherit = "tw.api.configuration"

    # 7: defaults methods   

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def action_login_ahm_portal(self):
        config = self.suspend_security().search([('api_type_id.value','=','ahm')], limit=1)
        if not config:
            return 0, 'Configuration API AHM belum dibuat.'

        url = config.base_url + config.client_id
        login_session = requests.Session()
        login_session.auth = (config.username, config.password)
        response = login_session.post(url)

        status_code = response.status_code
        content = json.loads(response.content)
        
        log_content = {
            'name': 'AHM Login Portal',
            'url': url,
            'response_code': str(status_code),
            # 'type': 'outgoing',
            'response': str(content)
        }
        if status_code == 200:
            if content.get('message')['message'] == 'GAGAL':
                self.env['tw.api.log'].sudo().create(log_content)
                return 0, 'Invalid Username / Password !'
            else:
                return 1, login_session
        else:
            self.env['tw.api.log'].sudo().create(log_content)
            return 0, 'Invalid Username / Password !'
        
    def proses_send_data_to_ahm_portal(self, url_proses_data, data):
        status, login_session = self.suspend_security().action_login_ahm_portal()
        if status == 0:
            self.env['tw.api.log'].suspend_security().invalid_post_response(
                name='Configuration API belum dibuat',
                url=self.base_url + self.client_id,
                response_code=0,
                # type='outgoing',
                response='Configuration API belum dibuat'
            )
            return
        
        url = self.base_url + url_proses_data
        jxid = login_session.cookies.get('JXID')
        tkid = login_session.cookies.get('TKID')
        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'JXID': jxid,
        }
        cookies = {
            'JXID': jxid,
            'TKID': tkid,
        }
        
        response = requests.post(url=url, json=data, headers=headers, cookies=cookies)
        status_code = response.status_code
        content = response.content
        return status_code, content


