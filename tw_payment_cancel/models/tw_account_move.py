# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# 4:  imports from odoo modules


# 5: local imports

# 6: Import of unknown third party lib

class InheritAccountMove(models.Model):
    _inherit = "account.move"
    
    # 7: defaults methods
    
    # 8: fields
    
    # 9: relation fields
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: private methods
    def _must_check_constrains_date_sequence(self):
        if self.env.context.get('skip_date_sequence_check', False):
            return False
        return True
    
    # 14: public methods
    
    # 15: computed methods
    