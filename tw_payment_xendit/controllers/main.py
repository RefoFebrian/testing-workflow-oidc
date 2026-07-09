import json
import logging
from werkzeug.exceptions import Forbidden
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class XenditController(http.Controller):

    @http.route('/api/ext/payment/xendit/callback/success', type='http', auth='public', methods=['GET'], csrf=False)
    def xendit_callback_success(self, **post):
        """ Handle Xendit callback """
        _logger.info('XENDIT callback received: %s', post)
        form_url = '/payment/status'
        model = post.get('model')
        id = post.get('id')
        action_id = post.get('action_id')
        view_type = post.get('view_type')
        trx = request.env[model].sudo().search([('id', '=', id)])
        if trx:
            trx.action_check_payment_status()
            base_url = http.request.httprequest.host_url
            form_url = f"{base_url}web#id={id}&model={model}&view_type={view_type}&action={action_id}"
            # Example : http://localhost:8069/web#id=56&model=tw.account.payment&view_type=form&action=802
        
        _logger.info('XENDIT callback redirect to: %s', form_url)
        return request.redirect(form_url)

    @http.route('/api/ext/payment/xendit/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def xendit_webhook(self, **post):
        """ Handle Xendit webhook """
        try:
            data = json.loads(request.httprequest.data)
            _logger.info('XENDIT webhook received: %s', data)

            # Verify the webhook signature
            verification_token = request.httprequest.headers.get('X-Callback-Token')
            if not verification_token:
                _logger.warning('Missing X-Callback-Token header')
                raise Forbidden()

            # Find the provider with this verification token
            provider = request.env['payment.provider'].sudo().search([
                ('code', '=', 'xendit'),
                ('xendit_verification_token', '=', verification_token)
            ], limit=1)

            if not provider:
                _logger.warning('Invalid verification token: %s', verification_token)
                raise Forbidden()

            # Process the webhook data
            external_id = data.get('external_id')
            status = data.get('status', '').lower()

            if not external_id:
                _logger.error('Missing external_id in webhook data')
                return json.dumps({'status': 'error', 'message': 'Missing external_id'})

            # Find the transaction
            tx = request.env['payment.transaction'].sudo().search([
                ('reference', '=', external_id),
                ('provider_code', '=', 'xendit')
            ], limit=1)

            if not tx:
                _logger.error('Transaction not found for reference: %s', external_id)
                return json.dumps({'status': 'error', 'message': 'Transaction not found'})

            # Update transaction status
            if status in ['completed', 'paid']:
                tx._set_done()
                if tx.invoice_ids:
                    tx.invoice_ids.filtered(
                        lambda inv: inv.state == 'draft'
                    ).sudo().action_post()
            elif status in ['failed', 'expired']:
                tx._set_canceled()
            elif status in ['pending']:
                tx._set_pending()

            tx.xendit_status = status
            tx.xendit_reference = data.get('qr_string', tx.xendit_reference)

            return json.dumps({'status': 'success'})

        except Exception as e:
            _logger.exception('Error processing XENDIT webhook: %s', str(e))
            return json.dumps({'status': 'error', 'message': str(e)})
