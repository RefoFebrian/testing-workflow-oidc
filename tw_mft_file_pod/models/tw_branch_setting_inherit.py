# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class BranchSettingInherit(models.Model):
    _inherit = "tw.branch.setting"

    # 7: defaults methods

    # 8: fields
    atpm_code_bundling = fields.Char(string="ATPM Code Bundling", default='16367', help='Kode ATPM dari Branch pada Bundling Production untuk kebutuhan MFT File POD')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods