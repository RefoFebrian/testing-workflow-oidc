# -*- coding: utf-8 -*-

import requests
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TwPrivacyPolicyController(http.Controller):
    """
    Controller untuk Privacy Policy check & acceptance di TETO system.
    Memanggil HOKI API untuk check dan accept privacy policy.
    """

    def _get_hoki_api_config(self):
        """
        Retrieve HOKI API configuration from tw.api.configuration.
        Returns configuration object or False if not found.
        """
        try:
            # Get HOKI API configuration using Selection model
            api_type_obj = request.env['tw.selection'].sudo().get_selection('ApiType', 'Hoki')
            if not api_type_obj:
                _logger.error("HOKI API type not found in tw.selection")
                return False
            
            config = request.env['tw.api.configuration'].sudo().search([
                ('api_type_id', '=', api_type_obj.id)
            ], limit=1)

            if not config:
                _logger.error("HOKI API configuration not found in tw.api.configuration")
                return False

            # Check if token exists, if not generate it
            if not config.token:
                _logger.info("No HOKI token found, generating new token...")
                config.action_get_token()

            return config

        except Exception as e:
            _logger.error("Error getting HOKI API config: %s", str(e), exc_info=True)
            return False

    def _is_token_error(self, response_data):
        """
        Detect if response indicates token error.
        
        HOKI API error format:
        {
            "status": 0,
            "message": "Failed",
            "code": 401,
            "data": {
                "error_descrip": "Token is expired or invalid!",
                "error": "invalid_token"
            }
        }
        """
        if not response_data:
            return False

        error_indicators = [
            'token is expired',
            'token expired',
            'invalid token',
            'token is invalid',
            'unauthorized',
            'authentication failed',
            'invalid_token'
        ]

        # Check HTTP code (401 = Unauthorized)
        if isinstance(response_data, dict):
            if response_data.get('code') == 401:
                return True

            # Check in data.error_descrip and data.error (HOKI API format)
            if 'data' in response_data and isinstance(response_data['data'], dict):
                data = response_data['data']
                error_msg = str(data.get('error_descrip', '')).lower()
                if not error_msg:
                    error_msg = str(data.get('error', '')).lower()

                if error_msg:
                    for indicator in error_indicators:
                        if indicator in error_msg:
                            return True

            # Check at root level
            error_msg = str(response_data.get('error', '')).lower()
            if not error_msg:
                error_msg = str(response_data.get('message', '')).lower()

            if error_msg:
                for indicator in error_indicators:
                    if indicator in error_msg:
                        return True

        return False

    def _call_hoki_check_api(self, login, config, retry_on_token_error=True):
        """
        Call HOKI API to check if user has accepted privacy policy.
        
        Args:
            login: User login/username
            config: tw.api.configuration object
            retry_on_token_error: Whether to retry on token error (default: True)
            
        Returns:
            dict: Response from HOKI API
                {
                    "is_accepted": bool,
                    "privacy_policy_id": int,
                    "privacy_policy_content": html_string
                }
        """
        try:
            url = f"{config.base_url.rstrip('/')}/api/1.0/privacy_policy"

            headers = {
                'access_token': config.token,
                'Content-Type': 'application/json'
            }

            payload = {
                "login": login,
                "type": "TETO TDM"  # Identify requests from TETO system
            }

            _logger.info("Calling HOKI check API for user: %s", login)
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            json_response = response.json()

            # Check for token error in response
            if self._is_token_error(json_response) and retry_on_token_error:
                _logger.warning("Token expired/invalid, regenerating token and retrying...")

                # Regenerate token
                config.action_get_token()

                # Retry with new token (only once to prevent infinite loop)
                return self._call_hoki_check_api(login, config, retry_on_token_error=False)

            # Extract result from HOKI response format
            if 'result' in json_response:
                return json_response['result']

            return json_response

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to call HOKI check API: %s", str(e), exc_info=True)
            return {'error': str(e)}
        except Exception as e:
            _logger.error("Unexpected error in HOKI check API: %s", str(e), exc_info=True)
            return {'error': str(e)}

    def _call_hoki_accept_api(self, login, privacy_policy_id, config, retry_on_token_error=True):
        """
        Call HOKI API to accept privacy policy.
        
        Args:
            login: User login/username
            privacy_policy_id: ID of privacy policy to accept
            config: tw.api.configuration object
            retry_on_token_error: Whether to retry on token error (default: True)
            
        Returns:
            dict: Response from HOKI API
                {
                    "is_accepted": bool
                }
        """
        try:
            url = f"{config.base_url.rstrip('/')}/api/1.0/accept_privacy_policy"

            headers = {
                'access_token': config.token,
                'Content-Type': 'application/json'
            }

            payload = {
                "login": login,
                "type": "TETO TDM",  # Identify requests from TETO system
                "privacy_policy_id": privacy_policy_id
            }

            _logger.info("Calling HOKI accept API for user: %s, policy_id: %s", login, privacy_policy_id)
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            json_response = response.json()

            # Check for token error in response
            if self._is_token_error(json_response) and retry_on_token_error:
                _logger.warning("Token expired/invalid, regenerating token and retrying...")

                # Regenerate token
                config.action_get_token()

                # Retry with new token (only once to prevent infinite loop)
                return self._call_hoki_accept_api(login, privacy_policy_id, config, retry_on_token_error=False)

            # Extract result from HOKI response format
            if 'result' in json_response:
                return json_response['result']

            return json_response

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to call HOKI accept API: %s", str(e), exc_info=True)
            return {'error': str(e)}
        except Exception as e:
            _logger.error("Unexpected error in HOKI accept API: %s", str(e), exc_info=True)
            return {'error': str(e)}

    @http.route('/tw/check_privacy_policy', type='json', auth='user', methods=['POST'])
    def check_privacy_policy(self, **kwargs):
        """
        Check if logged-in user has accepted current privacy policy.
        Called by JavaScript after user login.
        
        Returns:
            dict: {
                'status': 'success'|'error',
                'is_accepted': bool,
                'privacy_policy_id': int|False,
                'privacy_policy_content': html_string|False,
                'message': error message if any
            }
        """
        try:
            # Get logged-in user
            user = request.env.user
            if not user or not user.login:
                return {
                    'status': 'error',
                    'is_accepted': False,
                    'message': 'User not authenticated'
                }

            login = user.login

            # Get HOKI API configuration
            config = self._get_hoki_api_config()
            if not config:
                _logger.warning("HOKI API not configured, skipping privacy policy check")
                return {
                    'status': 'success',
                    'is_accepted': True,  # Allow user to continue if API not configured
                    'message': 'HOKI API not configured'
                }

            # Call HOKI check API
            hoki_response = self._call_hoki_check_api(login, config)

            if hoki_response.get('error'):
                _logger.warning("HOKI API error: %s. Allowing user to continue.", hoki_response.get('error'))
                return {
                    'status': 'success',
                    'is_accepted': True,  # Allow user to continue on error
                    'message': hoki_response.get('error')
                }

            # Parse HOKI response
            # Expected format from HOKI:
            # {
            #     "status": 1,
            #     "code": 200,
            #     "data": {
            #         "is_accepted": bool,
            #         "privacy_policy_id": int,
            #         "privacy_policy_content": html
            #     }
            # }
            data = hoki_response.get('data', hoki_response)

            return {
                'status': 'success',
                'is_accepted': data.get('is_accepted', True),
                'privacy_policy_id': data.get('privacy_policy_id', False),
                'privacy_policy_content': data.get('privacy_policy_content', False)
            }

        except Exception as e:
            _logger.error("Error checking privacy policy: %s", str(e), exc_info=True)
            return {
                'status': 'error',
                'is_accepted': True,  # Allow user to continue on error
                'message': str(e)
            }

    @http.route('/tw/accept_privacy_policy', type='json', auth='user', methods=['POST'])
    def accept_privacy_policy(self, privacy_policy_id=None, **kwargs):
        """
        Accept privacy policy for logged-in user.
        Called by JavaScript when user clicks "Accept" button.
        
        Args:
            privacy_policy_id: ID of privacy policy to accept
            
        Returns:
            dict: {
                'status': 'success'|'error',
                'is_accepted': bool,
                'message': error message if any
            }
        """
        try:
            # Get logged-in user
            user = request.env.user
            if not user or not user.login:
                return {
                    'status': 'error',
                    'is_accepted': False,
                    'message': 'User not authenticated'
                }

            login = user.login

            if not privacy_policy_id:
                return {
                    'status': 'error',
                    'is_accepted': False,
                    'message': 'Privacy Policy ID is required'
                }

            # Get HOKI API configuration
            config = self._get_hoki_api_config()
            if not config:
                _logger.warning("HOKI API not configured, cannot accept privacy policy")
                return {
                    'status': 'error',
                    'is_accepted': False,
                    'message': 'HOKI API not configured'
                }

            # Call HOKI accept API
            hoki_response = self._call_hoki_accept_api(login, privacy_policy_id, config)

            if hoki_response.get('error'):
                return {
                    'status': 'error',
                    'is_accepted': False,
                    'message': hoki_response.get('error')
                }

            # Parse HOKI response
            # Expected format from HOKI:
            # {
            #     "status": 1,
            #     "code": 200,
            #     "data": {
            #         "is_accepted": bool
            #     }
            # }
            data = hoki_response.get('data', hoki_response)

            is_accepted = data.get('is_accepted', False)

            if is_accepted:
                _logger.info("User %s accepted privacy policy %s", login, privacy_policy_id)
                return {
                    'status': 'success',
                    'is_accepted': True,
                    'message': 'Privacy policy accepted successfully'
                }
            else:
                return {
                    'status': 'error',
                    'is_accepted': False,
                    'message': 'Failed to accept privacy policy'
                }

        except Exception as e:
            _logger.error("Error accepting privacy policy: %s", str(e), exc_info=True)
            return {
                'status': 'error',
                'is_accepted': False,
                'message': str(e)
            }
