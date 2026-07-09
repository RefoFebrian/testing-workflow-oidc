# -*- coding: utf-8 -*-

# 1: imports of python lib
import traceback
import logging

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, api

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwIrCron(models.Model):
    """Inherit ir.cron untuk menangkap error dan mencatat ke tw.cron.log."""
    
    _inherit = "ir.cron"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields   

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def method_direct_trigger(self):
        """
        Override method_direct_trigger untuk menangkap error dari manual trigger.
        Error akan di-log ke tw.cron.log sebelum di-raise kembali.
        """
        self.ensure_one()
        try:
            return super().method_direct_trigger()
        except Exception as e:
            self._log_cron_error(e, trigger_type='manual')
            raise

    def _callback(self, cron_name, server_action_id):
        """
        Override _callback untuk menangkap error dari automatic cron execution.
        Method ini dipanggil oleh scheduler ketika cron berjalan otomatis.
        Error akan di-log ke tw.cron.log sebelum di-raise kembali.
        """
        self.ensure_one()
        try:
            return super()._callback(cron_name, server_action_id)
        except Exception as e:
            self._log_cron_error(e, trigger_type='automatic')
            raise

    # 13: action methods

    # 14: private methods
    def _log_cron_error(self, exception, trigger_type='unknown'):
        """
        Log error ke tw.cron.log.
        
        :param exception: Exception yang terjadi
        :param trigger_type: 'manual' atau 'automatic'
        """
        self.ensure_one()
        
        error_message = str(exception)
        error_detail = traceback.format_exc()
        
        # Get model_id from ir.actions.server
        model_id = False
        method_name = ''
        
        if self.ir_actions_server_id:
            server_action = self.ir_actions_server_id
            if server_action.model_id:
                model_id = server_action.model_id.id
            method_name = server_action.code or ''
        
        # Add trigger type info to error detail
        error_detail = f"[Trigger: {trigger_type}]\n\n{error_detail}"
        
        try:
            # Gunakan cursor baru untuk commit log error terpisah dari transaksi utama
            with self.pool.cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                new_env['tw.cron.log'].create_log(
                    cron_id=self.id,
                    model_id=model_id,
                    method_name=method_name[:500] if method_name else '',
                    error_message=error_message,
                    error_detail=error_detail,
                )
                new_cr.commit()
            _logger.info('Cron error logged for job %r (%s) [%s]', self.name, self.id, trigger_type)
        except Exception as log_error:
            # Jangan sampai logging error menggagalkan proses
            _logger.error('Failed to log cron error: %s', log_error)

