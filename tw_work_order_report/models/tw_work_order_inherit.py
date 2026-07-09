# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, api, _
from odoo.exceptions import ValidationError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwWorkOrderReportInherit(models.Model):
    _inherit = "tw.work.order"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_print_kwitansi(self):
        self.ensure_one()
        return self.env.ref('tw_work_order_report.action_print_wo_kwitansi').report_action(self)

    # 14: private methods
