import logging

from odoo import http, _
from odoo.http import request

from ast import literal_eval

from ...tw_api.controllers.response import Respapi, API_VERSION
from ...tw_api.controllers.check_token import AuthOauthCheckToken as auth

_logger = logging.getLogger(__name__)
version = API_VERSION

class WebTelegram(http.Controller):
    @http.route('/api/ext/telegram/action', type="http", auth="user", methods=['GET'], csrf=False)
    def telegram_action(self, **params):
        model = params.get('model')
        transaction_id = params.get('transaction_id')
        action = params.get('action')
        description = params.get('description') or 'Thankyou!'
        if not model or not transaction_id or not action:
            return Respapi.error(errorDescription='Mandatory paramaters not fullfilled')
        try:
            object = request.env[model].browse(int(transaction_id))
            class_method = getattr(object, action)
            class_method()
            html_code = self.get_success_html_response(description)
            return http.request.make_response(html_code, headers=[('Content-Type', 'text/html')])
        except Exception as e:
            request._cr.rollback()
            html_code = self.get_failed_html_response(description,e)
            return http.request.make_response(html_code, headers=[('Content-Type', 'text/html')])

    def get_success_html_response(self,description):
        img_src = "/web_telegram/static/src/img/success.png"
        title = "Your request is proced successfully."
        return self.get_html_response(img_src,title,description)

    def get_failed_html_response(self,description, error_message):
        img_src = "/web_telegram/static/src/img/failed.png"
        title = "Your request is failed to proced."
        return self.get_html_response(img_src,title,description,error_message)

    def get_html_response(self,img_src,title,description,error_message=""):
        return """
        <html><body>
            <style>
                .holder{
                width: 480px;
                text-align: center;
                margin: 0 auto;
                padding-top: 120px;
                }
                .holder h1 {
                font-family: 'loveloblack', sans-serif;
                font-size:5em;
                color:#2d2d2d;
                text-shadow: 3px 3px 0 #e3e3e3;
                line-height: 27px;
                margin-top: 12px;
                margin-bottom: 10px;
                }
                .holder h1 span.tbl{
                font-family: Dosis,Tahoma,sans-serif;
                font-size:35px;
                color:#2d2d2d;
                line-height:1em;
                font-weight: bold;
                letter-spacing: -1px;
                line-height: 1;
                text-shadow: -1px 1px 1px rgba(0, 0, 0, 0.3);
                }
                .holder h1 span {
                font-family: Dosis,Tahoma,sans-serif;
                font-size:1em;
                color:#3d9df8;
                line-height:1em;
                font-weight: bold;
                letter-spacing: -1px;
                line-height: 1;
                text-shadow: -1px 1px 1px rgba(0, 0, 0, 0.3);
                }  
                p{
                font-size: 18px;
                font-weight: 600;
                color: #86968f;
                font-family: 'Neuton', serif;
                }
            </style>
            <div class="holder">
                <img src="%s" style="width:250px;" />
                <h1><span class="tbl">%s</span></h1>
                <p><span class="tbl">%s</span></p>
                <p><span class="tbl" style="color:#397200">%s</span></p>
                <br>
                <br/>
            </div>
        </body></html>
        """%(img_src,title,error_message,description)
    