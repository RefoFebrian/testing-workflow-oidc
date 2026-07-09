# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class EmployeeAuthSignup(models.Model):
    _inherit = "hr.employee"

    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super(EmployeeAuthSignup, self).create(vals_list)
        for data in create:
            if data.user_id:
                user_obj = data.user_id
                user_obj = user_obj.action_generate_reset_password_user()
        return create

    def write(self, vals):
        user_id = self.user_id
        write = super(EmployeeAuthSignup, self).write(vals)
        if not user_id and vals.get('user_id') and self.user_id:
            user_obj = self.user_id
            user_obj = user_obj.action_generate_reset_password_user()
        return write

    # 13: action methods

    # 14: private methods