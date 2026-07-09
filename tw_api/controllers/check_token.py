
import functools
import logging
from http.client import UNAUTHORIZED
from mimetypes import init

from odoo.http import request, Controller
from ...tw_api.controllers.response import Respapi

ERR_TOKEN_MULTY = ("ETM","Invalid Token","Multi token, contact Administrator")
ERR_TOKEN_INVALID_FORMAT = ("ETIF","Invalid Token","Invalid token format")
ERR_TOKEN_NOT_FOUND_HEADER = ("ETNFH","Invalid Token","Missing token in request header")
ERR_TOKEN_NOT_FOUND_DATABASE = ("ETNFD","Invalid Token","Session not found")

_logger = logging.getLogger(__name__)
PREFIX = 'Bearer'


def get_token_from_bearer(header):
    bearer, _, token = header.partition(' ')
    if bearer != PREFIX:
        return '__Invalid Token'

    return token


class AuthOauthCheckToken(Controller):

    def check_token(func):
        @functools.wraps(func)
        def wrap(self, *args, **kwargs):
            access_token = get_token_from_bearer(
                request.httprequest.headers['Authorization']) if 'Authorization' in request.httprequest.headers else False
            if not access_token:
                return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_NOT_FOUND_HEADER)
            try:
                # verification token to provider
                token = request.env['res.users'].sudo().verify_token(
                    request.httprequest.headers['device_id'], access_token)

                if not token:
                    return Respapi.error(UNAUTHORIZED)
                if isinstance(token, Respapi):
                    return token

                # create session
                request.session.uid = token.user_id.id
                request.uid = token.user_id.id

                return func(self, *args, **kwargs)
            except ValueError as ve:
                return Respapi.error(UNAUTHORIZED, error=ERR_TOKEN_MULTY)
            except Exception as e:
                return Respapi.error(code=UNAUTHORIZED, error=str(e.args[0]['code']) if 'code' in e.args[0] else "Error", errorDescription=str(e.args[0]['message']) if 'message' in e.args[0] else e)
        return wrap
