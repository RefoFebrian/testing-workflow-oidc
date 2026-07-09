# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class ResArea(models.Model):
    _name = "res.area"
    _description = 'Res Area'
    _order = "id desc"
    _rec_names_search = ['name', 'code']

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    description = fields.Char(string='Description')
    company_ids = fields.Many2many('res.company', 'res_area_company_rel', 'area_id', 'company_id', "Branch", domain="[('parent_id','!=',False)]")

    # 9: relation fields

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Code tidak boleh ada yang sama.')
    ]

    @api.constrains('company_ids')
    def _check_company_ids(self):
        if len(self.company_ids) < 1:
            raise ValidationError(_('Branches must be fill.'))

    # 11: compute/depends & on change methods
    @api.depends('code', 'description')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}] {record.description}"

    # 12: override methods

    # 13: action methods

    # 14: private methods

