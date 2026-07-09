# 1: imports of python lib
import contextlib
import logging
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
_logger = logging.getLogger(__name__)

class ResUserEmployeeAuthSignup(models.Model):
    _inherit = "res.users"

    # 7: defaults methods
    
    # 8: fields
    reset_password_date = fields.Datetime(string='Reset Password Date')
    reset_password_url = fields.Char(string='Reset Password URL')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    
    # 12: override methods

    # 13: action methods

    # 14: private methods
    def action_generate_reset_password_user(self):
        send_email = self.env['ir.config_parameter'].sudo().get_param('tw_hr_auth_signup.send_reset_password_email', 'False').strip().lower() == 'true'
        for user in self:
            if user.partner_id:
                url = user.partner_id._get_signup_url()
                if url:
                    if 'reset_password' not in url:
                        slice_url = url.split('/web/')
                        url = slice_url[0] + '/web/reset_password?' + slice_url[1].split('?')[1]
                    vals = {'reset_password_url': url, 'reset_password_date': datetime.now()}
                    user.write(vals)
                    if send_email:
                        user.action_send_reset_password_instruction()
        return self

    def action_send_reset_password_instruction(self):
        for user in self:
            if user.email:
                email_values = {
                    'email_cc': False,
                    'auto_delete': False,
                    'message_type': 'user_notification',
                    'recipient_ids': [],
                    'partner_ids': [],
                    'scheduled_date': False,
                }

                email_values['email_to'] = user.email
                user_lang = user.lang or self.env.lang or 'en_US'
                body = self.env['mail.render.mixin'].with_context(lang=user_lang)._render_template(
                    self.env.ref('tw_hr_auth_signup.tw_reset_password_email'),
                    model='res.users', res_ids=user.ids,
                    engine='qweb_view', options={'post_process': True})[user.id]
                mail = self.env['mail.mail'].sudo().create({
                    'subject': self.with_context(lang=user_lang).env._('Password reset'),
                    'email_from': user.company_id.email_formatted or user.email_formatted,
                    'body_html': body,
                    **email_values,
                })
                mail.send()
                _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)
                message = _('A reset password link was sent by email')
            else:
                message = _('No email address found for user <%s>') % user.name
        
        _logger.info(message)

        