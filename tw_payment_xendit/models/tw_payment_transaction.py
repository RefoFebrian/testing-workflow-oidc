import requests
import pprint
import logging
import re
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo import tools
from odoo import http
from .. import const

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    note = fields.Text(string='Internal Note', help='Additional notes about this transaction')
    payment_url = fields.Char(
        string='Payment URL',
        readonly=True,
        copy=False,
        help='URL to redirect the customer for payment processing'
    )
    
    def action_open_payment_url(self):
        """Open the payment URL in a new tab.
        
        :return: A window action to open the payment URL
        :rtype: dict
        :raise: UserError if no payment URL is available
        """
        self.ensure_one()
        if not self.payment_url:
            raise UserError(_('No payment URL is available for this transaction.'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': self.payment_url,
            'target': 'self',
        }
    
    def action_check_payment_status(self):
        """Action to manually check payment status from Xendit.
        
        This can be called from a button in the UI.
        Uses the same notification processing as the webhook.
        """
        self.ensure_one()
        
        try:
            result = self._xendit_check_payment_status()
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
            
            # Process the notification data the same way the webhook does
            self._process_notification_data(result)
            
            return True
            
        except Exception as e:
            _logger.exception('Error checking payment status:')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to check payment status: %s') % str(e),
                    'sticky': False,
                    'type': 'danger',
                },
                'target': 'new',
            }

    def _get_payment(self):
        payment_ids = self.env['account.payment'].sudo().search([('payment_transaction_id', '=', self.id)])
        if not payment_ids:
            payment_ids = self.env['tw.account.payment'].sudo().search([('payment_transaction_id', '=', self.id)])
        return payment_ids
        
    def _xendit_prepare_invoice_request_payload(self):
        """Extend the payload for the invoice request to include QRIS specific parameters.

        :return: The updated request payload.
        :rtype: dict
        """
        # Get the original payload from the parent method
        payload = super()._xendit_prepare_invoice_request_payload()
        
        # Only process for Xendit QRIS payments
        if self.provider_code != 'xendit' or not hasattr(self, 'payment_method_code'):
            return payload
            
        # Update payload for QRIS payments
        # For available payment methods, please refer to Xendit documentation (https://docs.xendit.co/docs/payment-links-api-overview)
        payment_methods = const.PAYMENT_METHODS_MAPPING.get(self.payment_method_code) or [self.payment_method_code.upper()]
        if self.payment_method_code == 'xendit':
            payment_methods = ['QRIS','CARD']
            # Add E-Wallets
            payment_methods += ["OVO","DANA","SHOPEEPAY","LINKAJA","ASTRAPAY","NEXCASH","JENIUSPAY"]
            # Add Banks
            payment_methods += ["BNI","MANDIRI","PERMATA","BRI","BCA"]
            # Add Debit Cards
            payment_methods += ["DD_BRI","DD_MANDIRI"]

        payload.update({
            'payment_methods': payment_methods,
            'success_redirect_url': self._get_redirect_url(),
            'failure_redirect_url': self._get_redirect_url(),
        })
        
        # Add customer details if available
        if payload.get('customer') and payload.get('customer').get('addresses'):
            payload['customer'].pop('addresses')
            
        _logger.info('Xendit QRIS Request Payload: %s', pprint.pformat(payload))
        return payload
    
    def _get_redirect_url(self):
        base_url = http.request.httprequest.host_url
        callback_url = f"{base_url}api/ext/payment/xendit/callback/success"
        params = self._context.get('params')
        if not params or not params.get('id') or not params.get('model'):
            return base_url
        
        params_url = f"id={params.get('id')}&model={params.get('model')}&view_type=form"
        if self._context.get('action_id'):
            params_url += f"&action_id={self._context.get('action_id')}"
        
        form_url = f"{callback_url}?{params_url}"
        return form_url

    def _get_specific_rendering_values(self, processing_values):
        """Extend to handle QRIS specific rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        # Only process for Xendit QRIS payments
        if self.provider_code != 'xendit':
            return res
            
        # The parent method should have already set up the payment URL
        payment_url = res.get('api_url') or res.get('payment_url')
        if payment_url:
            # Update the payment URL in our transaction record
            self.sudo().write({
                'payment_url': payment_url,
                'state': 'pending',
            })
            _logger.info('QRIS Payment URL set: %s', payment_url)            
        return res
        
    def _xendit_check_payment_status(self):
        """Check payment status from Xendit API.
        
        This method calls Xendit's API to get the latest payment status.
        
        :return: Dictionary containing payment status and details
        :rtype: dict
        """
        self.ensure_one()
        
        if self.provider_code != 'xendit':
            _logger.warning('Cannot check status: Not a Xendit payment')
            return {}
            
        # Try to get the invoice ID from provider_reference or payment URL
        invoice_id = self.provider_reference
        if not invoice_id and self.payment_url:
            # Extract invoice ID from payment URL if available
            # Format: https://checkout-staging.xendit.co/web/INVOICE_ID
            match = re.search(r'/([a-f0-9]{24})$', self.payment_url)
            if match:
                invoice_id = match.group(1)
                # Save the extracted invoice ID as provider_reference for future use
                self.provider_reference = invoice_id
        
        if not invoice_id:
            _logger.warning('Cannot check status: Missing Xendit invoice ID')
            return {}
            
        try:
            # Prepare the request to get invoice status
            _logger.info('Checking Xendit payment status for invoice: %s', invoice_id)
            
            # Call Xendit API to get payment status
            # Use the official Xendit API URL
            base_url = "https://api.xendit.co"
            url = f"{base_url}/v2/invoices/{invoice_id}"
            try:
                auth = (self.provider_id.xendit_secret_key, '')
                response = requests.get(url, auth=auth, timeout=10)
                response.raise_for_status()
                response = response.json()
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                _logger.exception("Unable to reach Xendit API endpoint")
                return {}
            except requests.exceptions.HTTPError as err:
                _logger.exception("Xendit API request failed with status %s", err.response.status_code)
                return {}
            except Exception as e:
                _logger.exception("Error calling Xendit API: %s", str(e))
                return {}
            
            _logger.info('Xendit payment status check response: %s', pprint.pformat(response))
            
            if not response:
                _logger.error('Empty response from Xendit API')
                return {}
                
            # Update payment URL if not set
            if not self.payment_url and response.get('invoice_url'):
                self.payment_url = response.get('invoice_url')
            
            # Update payment amount if different
            amount = float(response.get('amount', 0))
            if amount and amount != self.amount:
                _logger.info('Updating payment amount from %s to %s', self.amount, amount)
                self.amount = amount
                
            # The actual status update will be handled by _process_notification_data()
            # which is called from action_check_payment_status()
            return response
            
        except Exception as e:
            _logger.error('Error checking Xendit payment status: %s', str(e), exc_info=True)
            return {}
    
    def _process_notification_data(self, notification_data):
        """ Override to process the transaction based on Xendit data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data were received.
        """
        self.ensure_one()

        if self.provider_code != 'xendit':
            return super()._process_notification_data(notification_data)
            
        # Update the provider reference.
        self.provider_reference = notification_data.get('id')

        # Update payment method.
        payment_method_code = notification_data.get('payment_method', '')
        self._get_payment().message_post(body="Payment processed via Xendit with %s." % payment_method_code)
        
        # Update the payment state.
        payment_status = notification_data.get('status')
        if payment_status in const.PAYMENT_STATUS_MAPPING['pending']:
            self._set_pending()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['done']:
            if self.tokenize:
                self._xendit_tokenize_from_notification_data(notification_data)
            self._set_done()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['cancel']:
            self._set_canceled()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['error']:
            failure_reason = notification_data.get('failure_reason')
            self._set_error(_(
                "An error occurred during the processing of your payment (%s). Please try again.",
                failure_reason,
            ))
    
    def _set_canceled(self, state_message=None, extra_allowed_states=()):
        canceled = super()._set_canceled(state_message, extra_allowed_states)
        for trx in self:
            trx.reference = 'X'+trx.reference            
        return canceled

    def _set_done(self, state_message=None, extra_allowed_states=()):
        """Update the transaction state to 'done' and post the linked payment if exists.
        
        This method extends the default _set_done to automatically post the linked
        account.payment when the transaction is marked as done.
        
        :param str state_message: Optional message about the state change
        :param tuple extra_allowed_states: Extra states that can transition to 'done'
        :return: Updated transactions
        :rtype: recordset of payment.transaction
        """
        # Call parent's _set_done first
        super()._set_done(state_message, extra_allowed_states)
        
        payment_ids = self._get_payment()

        # Auto-post linked account.payment records that are in draft state
        for payment_id in payment_ids:
            try:
                if payment_id.state in ('draft', 'open', 'in_process'):
                    payment_id.action_validate()
                    _logger.info('Auto-posted payment %s for transaction %s', payment_id.name, self.reference)
            except Exception as e:
                self.env.cr.rollback()
                _logger.error('Failed to auto-post payment %s: %s', payment_id.name, str(e))
        
        return self
