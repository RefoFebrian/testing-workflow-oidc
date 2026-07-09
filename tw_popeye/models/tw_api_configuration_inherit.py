# -*- coding: utf-8 -*-

from odoo import models, fields
import requests
import json
class TwApiConfiguration(models.Model):
    _inherit = "tw.api.configuration"


    def action_get_token_popeye(self, is_return_token=False):
        url = "%s/api/v1/get_token" %self.base_url
        if self.auth_url:
            url = "%s%s" %(self.base_url,self.auth_url)

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        headers = {
            'content-type': "application/json",
        }
        request_data = requests.post(url, json=payload, headers=headers)
        
        if request_data.status_code == 400:
            raise Warning("URL Not Found")

        content = request_data.content
        response_content = json.loads(content)
        if 'data' in response_content:
            response_content = response_content['data']
        
        if request_data.status_code == 200:
            self.suspend_security().write({
                'token' :response_content.get('token'),
                'expired_on' :response_content.get('expired_on')
            })
            if is_return_token:
                return self.token
        else:
            raise Warning('Get Token Status %s ,Error %s'%(request_data.status_code,response_content.get('error_descrip')))

    def action_open_config_parameter_url_popeye(self):
        self.ensure_one()
        list_view_id = self.env.ref('base.view_ir_config_list').id
        form_view_id = self.env.ref('base.view_ir_config_form').id
        search_view_id = self.env.ref('base.view_ir_config_search').id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.config_parameter',
            'view_type': 'form',
            'view_mode': 'list,form',
            'domain': [('key','like','popeye')],
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id
        }
