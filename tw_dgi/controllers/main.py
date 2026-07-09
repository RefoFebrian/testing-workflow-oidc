# -*- coding: utf-8 -*-
import functools
import hashlib
import logging

from odoo.http import request

_logger = logging.getLogger(__name__)


def check_valid_dgi(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        headers = request.httprequest.headers

        api_key = headers.get('DGI-API-Key')
        api_token = headers.get('DGI-API-Token')
        epoch = headers.get('X-Request-Time')

        if not api_key:
            _logger.warning("DGI Auth: Missing DGI-API-Key header")
            return {'status': 0, 'message': 'Missing DGI-API-Key in request header!'}
        if not api_token:
            _logger.warning("DGI Auth: Missing DGI-API-Token header")
            return {'status': 0, 'message': 'Missing DGI-API-Token in request header!'}
        if not epoch:
            _logger.warning("DGI Auth: Missing X-Request-Time header")
            return {'status': 0, 'message': 'Missing X-Request-Time in request header!'}

        # Lookup API configuration by api_key
        api_config = request.env['tw.api.configuration'].sudo().search([
            ('api_key', '=', api_key),
        ], limit=1)

        if not api_config:
            _logger.warning("DGI Auth: API Key '%s' not recognized", api_key)
            return {'status': 0, 'message': f"API Key '{api_key}' not recognized!"}

        # Validate signature if api_secret is configured
        api_secret = api_config.api_secret or ''
        # Sender format: SHA256("api_key:api_secret:epoch")
        expected_token = hashlib.sha256(
            f"{api_key}:{api_secret}:{epoch}".encode()
        ).hexdigest()

        if api_token != expected_token:
            _logger.warning("DGI Auth: Invalid token for API Key '%s'", api_key)
            return {'status': 0, 'message': 'Invalid DGI-API-Token!'}

        # Set session user from config if available
        if api_config.user_id:
            request.update_env(user=api_config.user_id.id)

        _logger.info("DGI Auth: Successfully authenticated API Key '%s'", api_key)
        return func(self, *args, **kwargs)

    return wrap
