# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class ApiConfigurationInherit(models.Model):
    _inherit = "tw.api.configuration"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_actual_bank_name(self, bank_name):
        bank_name = super()._get_actual_bank_name(bank_name)
        if 'ASTRAPAY' in bank_name:
            bank_name = 'astrapay'

        return bank_name

    def _get_timestamp_qris_token(self):
        timestamp = super()._get_timestamp_qris_token()
        if self:
            if self.api_type_value.upper() == 'ASTRAPAY' and self.is_api_payment:
                if not timestamp:
                    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                new_timestamp = (datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ') + relativedelta(hours=7)).isoformat()
                timestamp = new_timestamp[:-7] + '+07:00'

        return timestamp
    
    def _get_log_name_generate_qris_token(self):
        log_name = super()._get_log_name_generate_qris_token()
        if self:
            if self.api_type_value.upper() == 'ASTRAPAY' and self.is_api_payment:
                log_name = 'Generate QRIS Token AstraPay'

        return log_name