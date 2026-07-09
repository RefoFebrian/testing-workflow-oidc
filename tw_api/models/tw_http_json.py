import json
from odoo.http import JsonRPCDispatcher, Request, Response
from odoo.tools import json_default
import werkzeug.datastructures

def _response(self, result=None, error=None):
    error_code = error.get('code',0) if error else 0
    if self.request_id is None and error_code != 100:
        response = result if error is None else error
    else:
        response = {'jsonrpc': '2.0', 'id': self.request_id}
        if error is not None:
            response['error'] = error
        if result is not None:
            response['result'] = result


    return self.request.make_json_response(response)

def make_json_response(self, data, headers=None, cookies=None, status=200):
    if type(data) == Response:
        if data.status_code:
            status = data.status_code
        data = json.loads(data.response[0])
    data = json.dumps(data, ensure_ascii=False, default=json_default)

    headers = werkzeug.datastructures.Headers(headers)
    headers['Content-Length'] = len(data)
    if 'Content-Type' not in headers:
        headers['Content-Type'] = 'application/json; charset=utf-8'
        
    return self.make_response(data, headers.to_wsgi_list(), cookies, status)

JsonRPCDispatcher._response = _response
Request.make_json_response = make_json_response