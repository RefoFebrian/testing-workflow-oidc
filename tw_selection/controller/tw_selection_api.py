import functools
import odoo
from odoo import http
from odoo.http import request
from odoo.http import Response
import werkzeug.wrappers
try:
    import simplejson as json
except ImportError:
    import json
import logging
from odoo.addons.rest_api.rest_exception import invalid_response
from odoo.addons.rest_api.controllers.main import *
_logger = logging.getLogger(__name__)


class ControllerREST(http.Controller):
    @http.route('/api/master/<version>/get_selection', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_selection(self, version, **post):
        selection_type = post.get('type')
        if not selection_type:
            info = 'Parameter "type" is not supplied!'
            return invalid_response(401,info)
        
        WHERE = f" WHERE type = '{selection_type}' AND active"
        
        if post.get('string'):
            WHERE += f" AND name ilike '%%{post.get('string')}%%'"

        limit = 10
        offset = 0

        if post.get('limit'):
            limit = int(post.get('limit'))

        if post.get('offset'):
            offset = int(post.get('offset'))

        query = f"""
            SELECT id
                , name
            FROM tw_selection 
            {WHERE}
            LIMIT {limit} OFFSET {offset}
        """
        request._cr.execute (query)
        ress =  request._cr.dictfetchall()

        return valid_response(200,ress) 
