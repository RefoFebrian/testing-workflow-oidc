# from odoo import http
import json
import logging
from datetime import date

from odoo import http, _
from odoo.http import request
from odoo.addons.website_self_register.controllers.controllers import WebsiteForm as SelfRegisterWebsite

_logger = logging.getLogger(__name__)


class InheritWebsiteForm(SelfRegisterWebsite):
    @http.route('/post-self-register', methods=['POST'], type='json', auth='public', website=True, csrf=False)
    def post_self_register(self, **post):

        # The parent returns a tuple (status, data)
        status, post_response = super(InheritWebsiteForm, self).post_self_register(**post)
        
        # * Send WA when success
        no_self_register = post_response.get('no_self_register', False)
        if status == 200 and no_self_register:
            try:
                name_customer = post_response.get('name_customer', False)
                no_telp = post_response.get('no_telp', False)
                template_self_register = request.env.ref('website_self_register_whatsapp_api.tw_whatsapp_content_template_self_register', raise_if_not_found=False)

                if template_self_register and no_telp:
                    pesan = template_self_register.content or ''
                    pesan = pesan.replace('{{1}}', str(name_customer or ''))
                    pesan = pesan.replace('{{2}}', str(no_self_register))

                    # Search using correct model name 'tw.whatsapp.message'
                    # and check message_type='outbox'
                    wa_message_model = request.env['tw.whatsapp.message'].suspend_security()
                    is_exist_wa_data = wa_message_model.search([
                        ('name', '=', name_customer),
                        ('phone_number', '=', no_telp),
                        ('message_type', '=', 'outbox'),
                        ('date', '=', date.today()),
                        ('origin', '=', no_self_register)
                    ], limit=1)
                    
                    if not is_exist_wa_data:
                        message_data = {
                            'name': name_customer,
                            'phone_number': no_telp,
                            'message': pesan,
                            'message_type': 'outbox',
                            'date': date.today(),
                            'state': 'draft', # Model default is draft
                            'note': 'Self Register',
                            'template_id': template_self_register.id,
                            'origin': no_self_register,
                        }
                        wa_message_model.create(message_data)
            except Exception as e:
                _logger.error("Error creating WhatsApp notification: %s", str(e))

        return status, post_response