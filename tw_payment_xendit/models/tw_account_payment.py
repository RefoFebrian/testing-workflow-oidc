from odoo import http, api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
import pprint

_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        super().action_post()
        if self.payment_method_line_id.payment_provider_id.code == 'xendit' :
            if not self.payment_transaction_id:
                return self.action_create_xendit_payment()
            # TODO : the action_open_payment_url its not working when called on action_post
            return self.action_open_payment_url()

    def action_create_xendit_payment(self):
        """Create a QRIS payment using Xendit payment provider"""
        self.ensure_one()
        if self.payment_transaction_id:
            # TODO : the action_open_payment_url its not working when called on action_post
            return self.action_open_payment_url()

        if self.state not in self._get_unconfirmed_states():
            raise UserError(_('Only draft payments can be paid with Xendit.'))
        
        if not self.partner_id:
            raise UserError(_('Partner is required for Xendit payment.'))

        if self.amount < 1:
            raise UserError(_('Silahkan isi amount yang valid'))
        
        if self.payment_method_id.code == 'qris' and self.amount > 10000000:
            raise UserError(_('Limit Amount for QRIS payment is 10,000,000.'))
        
        xendit_provider = self.payment_method_line_id.payment_provider_id

        # Get or create QRIS payment method
        payment_method = self.env['payment.method'].search([
            ('code', '=', self.payment_method_id.code),
            ('provider_ids', 'in', xendit_provider.id),
        ], limit=1)
        
        if not payment_method:
            payment_method = self.env['payment.method'].create({
                'name': self.payment_method_id.name,
                'code': self.payment_method_id.code,
                'provider_ids': [(6, 0, [xendit_provider.id])],
                'active': True,
                'support_tokenization': False,
                'support_express_checkout': False,
            })
        
        # Prepare transaction values
        name = self.name if (self.name and self.name != '/') else f'PAY-{self.id}'
        tx_values = {
            'provider_id': xendit_provider.id,
            'payment_method_id': payment_method.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'reference': name,
            # Name di note adalah nomor yang dikirim ke xendit
            'note': self.payment_method_id.name + ' of ' + self.partner_id.name + ' '+fields.Datetime.now().strftime('%Y-%m-%d ')+ ' '+name+ ' '+fields.Datetime.now().strftime('%H:%M'),
            'state': 'draft',
            'payment_method_code': self.payment_method_id.name,
        }

        # Add partner details for Xendit
        if self.partner_id.email:
            tx_values['partner_email'] = self.partner_id.email
        if self.partner_id.phone or self.partner_id.mobile:
            tx_values['partner_phone'] = self.partner_id.phone or self.partner_id.mobile
        if self.partner_id.city:
            tx_values['partner_city'] = self.partner_id.city
        if self.partner_id.country_id:
            tx_values['partner_country_id'] = self.partner_id.country_id.id
        if self.partner_id.zip:
            tx_values['partner_zip'] = self.partner_id.zip
        if self.partner_id.state_id:
            tx_values['partner_state_id'] = self.partner_id.state_id.id
        if self.partner_id.street:
            tx_values['partner_address'] = self.partner_id.street

        add_context = {'params':{
            'id': self.id,
            'model': self._name,
        }}

        # Create payment transaction
        transaction = self.env['payment.transaction'].with_context(**add_context).create(tx_values)
        self.payment_transaction_id = transaction.id
        
        try:
            # Let Xendit handle the payment flow
            rendering_values = transaction._get_specific_rendering_values({})
            return {
                'type': 'ir.actions.act_url',
                'url': rendering_values.get('api_url', ''),
                'target': 'self',
            }
        except Exception as e:
            self.payment_transaction_id = False
            transaction.unlink()
            _logger.exception("Failed to create Xendit payment")
            raise UserError(_('Failed to create Xendit payment: %s') % str(e))

    def action_cancel_online_payment(self):
        self.ensure_one()
        if not self.payment_transaction_id:
            raise UserError(_('No payment transaction found for this payment.'))
        
        self.payment_transaction_id._set_canceled()
        self.payment_transaction_id = False

    def action_open_payment_url(self):
        """Open the payment URL in a new tab."""
        self.ensure_one()
        if not self.payment_transaction_id:
            raise UserError(_('No payment transaction found for this payment.'))
        
        # Ensure we're returning a client action
        action = self.payment_transaction_id.action_open_payment_url()
        return action
    
    def action_check_payment_status(self):
        """ Check the payment status from Xendit for this payment """
        self.ensure_one()
        if not self.payment_transaction_id:
            raise UserError(_('No payment transaction found for this payment.'))
            
        # Call the payment transaction's check status method
        result = self.payment_transaction_id.action_check_payment_status()
        
        # If there's no result, it means there was an error checking the status
        if not result:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Could not check payment status. Please try again later.'),
                    'sticky': False,
                    'type': 'danger',
                }
            }
        return result
    
    def action_view_payment_transaction(self):
        """View the QRIS payment transaction"""
        self.ensure_one()
        if not self.payment_transaction_id:
            raise UserError(_('No payment transaction found.'))
            
        return {
            'name': _('Payment Transaction'),
            'view_mode': 'form',
            'res_model': 'payment.transaction',
            'res_id': self.payment_transaction_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
    
    # Private method
    # TODO : Buat cron nya
    def schedule_check_qris_payments(self):
        """Cron job to check status of pending QRIS payments"""
        pending_payments = self.search([
            ('state', '=', 'open'),
            ('payment_transaction_id', '!=', False),
            ('payment_transaction_status', 'in', ['pending', 'authorized'])
        ])
        for payment in pending_payments:
            try:
                # TODO : get status from xendit
                payment.payment_transaction_id._get_tx_status()
                if payment.payment_transaction_status == 'done':
                    payment.action_validate()
            except Exception as e:
                _logger.error("Error checking QRIS payment status: %s", str(e))
