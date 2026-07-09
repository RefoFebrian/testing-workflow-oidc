from odoo import models, fields, api, _
import contextlib
import logging
_logger = logging.getLogger(__name__)

class TwUsers(models.Model):
    _inherit= "res.users"
    
    def _action_reset_password(self, signup_type="reset"):
        """ create signup token for each user, and send their signup url by email """
        if self.env.context.get('install_mode') or self.env.context.get('import_file'):
            return
        if self.filtered(lambda user: not user.active):
            raise UserError(_("You cannot perform this action on an archived user."))
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        self.mapped('partner_id').signup_prepare(signup_type=signup_type)

        # send email to users with their signup url
        account_created_template = None
        if create_mode:
            account_created_template = self.env.ref('auth_signup.set_password_email', raise_if_not_found=False)
            if account_created_template and account_created_template._name != 'mail.template':
                _logger.error("Wrong set password template %r", account_created_template)
                return

        email_values = {
            'email_cc': False,
            'auto_delete': True,
            'message_type': 'user_notification',
            'recipient_ids': [],
            'partner_ids': [],
            'scheduled_date': False,
        }

        for user in self:
            if user.email:
                email_values['email_to'] = user.email
                with contextlib.closing(self.env.cr.savepoint()):
                    if account_created_template:
                        account_created_template.send_mail(
                            user.id, force_send=True,
                            raise_exception=True, email_values=email_values)
                    else:
                        user_lang = user.lang or self.env.lang or 'en_US'
                        body = self.env['mail.render.mixin'].with_context(lang=user_lang)._render_template(
                            self.env.ref('auth_signup.reset_password_email'),
                            model='res.users', res_ids=user.ids,
                            engine='qweb_view', options={'post_process': True})[user.id]
                        mail = self.env['mail.mail'].sudo().create({
                            'subject': self.with_context(lang=user_lang).env._('Password reset'),
                            'email_from': user.company_id.email_formatted or user.email_formatted,
                            'body_html': body,
                            **email_values,
                        })
                        mail.send()
                if signup_type == 'reset':
                    _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)
                    message = _('A reset password link was sent by email')
                else:
                    _logger.info("Signup email sent for user <%s> to <%s>", user.login, user.email)
                    message = _('A signup link was sent by email')
            else:
                message = _('No email address found for user <%s>') % user.name
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Notification',
                'message': message,
                'sticky': False
            }
        }