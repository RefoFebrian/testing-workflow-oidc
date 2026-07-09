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


class PaymentProviderInherit(models.Model):
    _inherit = "payment.provider"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    api_payment_setting_ids = fields.One2many(
        comodel_name='tw.setting.api.payment',
        inverse_name='payment_provider_id',
        string='API Payment Settings',
        help="List of API Payment settings. Used for storing API Payment credentials. (e.g. AstraPay)"
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods