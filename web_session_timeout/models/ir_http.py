from odoo import models, http
from odoo.http import request
import time
import logging

_logger = logging.getLogger(__name__)

class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        # Perform standard authentication first
        super()._authenticate(endpoint)
        
        # Check server-side session timeout if configured
        # This acts as an active enforcement of inactivity timeout
        if request.session.uid:
            try:
                ICP = request.env['ir.config_parameter'].sudo()
                max_timeout = int(ICP.get_param('sessions.max_timeout_seconds', 0))
                
                if max_timeout > 0:
                    # Check session last modification time from the store
                    session_store = http.root.session_store
                    if hasattr(session_store, 'get_session_filename'):
                        path = session_store.get_session_filename(request.session.sid)
                        import os
                        if os.path.exists(path):
                            last_modified = os.path.getmtime(path)
                            if time.time() - last_modified > max_timeout:
                                _logger.info("Session %s expired due to max_timeout_seconds enforcement.", request.session.sid)
                                request.session.logout(keep_db=True)
                                raise http.SessionExpiredException("Session expired")
            except Exception as e:
                # Fallback safely if something goes wrong during the check
                _logger.warning("Error checking session timeout: %s", e)

    def session_info(self):
        result = super().session_info()
        ICP = self.env['ir.config_parameter'].sudo()
        
        # Idle timeout: client-side inactivity
        idle_limit = ICP.get_param('web_session_timeout.max_idle_timeout_seconds')
        try:
             result['session_idle_timeout_seconds'] = int(idle_limit) if idle_limit else 7200
        except ValueError:
             result['session_idle_timeout_seconds'] = 7200 # 2 hours default
             
        # Max timeout: server-side session lifetime
        max_limit = ICP.get_param('web_session_timeout.max_timeout_seconds')
        if max_limit:
            try:
                result['session_max_timeout_seconds'] = int(max_limit)
            except ValueError:
                result['session_max_timeout_seconds'] = 72000 # 20 hours default
                
        return result
