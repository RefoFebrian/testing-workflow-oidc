# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models, SUPERUSER_ID
_logger = logging.getLogger(__name__)

from ..base_suspend_security import BaseSuspendSecurityUid


class Base(models.AbstractModel):

    _inherit = "base"

    @api.model
    def suspend_security(self):
        #Avoid error when Suspend security used in API, which dont have self.env.uid
        user_id = self.env.uid if self.env.uid else SUPERUSER_ID
        return self.with_env(api.Environment(self.env.cr,BaseSuspendSecurityUid(user_id),self.env.context))

    def sudo(self, flag=True):
        if isinstance(SUPERUSER_ID, BaseSuspendSecurityUid):
            return self.with_env(
                api.Environment(
                    self.env.cr, SUPERUSER_ID, self.env.context
                )
            )
        if not isinstance(flag, bool):
            _logger.warning("deprecated use of sudo(user), use with_user(user) instead", stack_info=True)
            return self.with_user(flag)
        return self.with_env(self.env(su=flag))
