# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class ApprovalSpDigital(models.Model):
    _inherit = "tw.approval"

    # 7: defaults methods

    # 8: fields
    
    # Audit Trail

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    # def update_record_with_value_from_context(self, trx, context):
    #     update_value = context.get('update_value', False)
    #     if update_value:
    #         if self.reason:
    #             update_value.update({'alasan_reject': self.reason})
        
    #     super(ApprovalSpDigital, self).update_record_with_value_from_context(trx, context)

    # 14: private methods