# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwSaleOrderInherit(models.Model):
    _inherit = "tw.sale.order"

    # 7: defaults methods  

    # 8: fields
    state_pod_mft = fields.Boolean(string='MFT AHM POD', default=True)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_confirm(self):
        confirm = super(TwSaleOrderInherit, self).action_confirm()
        self.suspend_security().write({'state_pod_mft': False})
        
        return confirm