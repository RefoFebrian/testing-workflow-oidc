# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from .. import const

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class PaymentProviderInherit(models.Model):
    _inherit = "payment.provider"

    # 7: defaults methods

    # 8: fields
    code = fields.Selection(
        selection_add=[('astrapay', 'AstraPay')], ondelete={'astrapay': 'set default'}
    )

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'astrapay').support_tokenization = True

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'astrapay':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies
    
    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'astrapay':
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES
    
    def _get_redirect_form_view(self, is_validation=False):
        """ Override of `payment` to avoid rendering the form view for validation operations.
        Note: `self.ensure_one()`
        :param bool is_validation: Whether the operation is a validation.
        :return: The view of the redirect form template or None.
        :rtype: ir.ui.view | None
        """
        self.ensure_one()

        if self.code == 'astrapay' and is_validation:
            return None
        return super()._get_redirect_form_view(is_validation)