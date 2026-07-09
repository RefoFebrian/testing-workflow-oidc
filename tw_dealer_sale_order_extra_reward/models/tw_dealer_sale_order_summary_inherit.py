# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwDealerSaleOrderSummaryInherit(models.Model):
    _inherit = "tw.dealer.sale.order.summary"

    # 7: defaults methods

    # 8: fields
    extra_reward = fields.Float('Beban Extra Reward')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods