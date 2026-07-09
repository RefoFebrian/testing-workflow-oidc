# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwTargetSalesPeople(models.Model):
    _name = "tw.target.sales.people"
    _description = "Target Sales People"

    # 7: defaults methods
    def _get_default_company(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False  

    # 8: fields

    # 9: relation fields
    job_id = fields.Many2one(comodel_name='hr.job', string='Job')
    company_id = fields.Many2one(comodel_name='res.company', string="Branch", default=_get_default_company)

    target_line_ids = fields.One2many(comodel_name='tw.target.sales.people.line', inverse_name='target_id', string='Target Lines')

    # 10: constraints & sql constraints
    @api.constrains('company_id','job_id')
    def company_name_unique(self):
        for target in self:
            data_count = self.search_count([('company_id', '=', target.company_id.id),('job_id', '=', target.job_id.id)])
            if data_count > 1:
                raise ValidationError("Target Company / Job tidak boleh duplikat !")

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals):
        create = super(TwTargetSalesPeople, self).create(vals)
        if create.target_line_ids:
            tipe = []
            for line in create.target_line_ids:
                key = (line.type, line.category_id.id, line.target_type)
                if key in tipe:
                    raise Warning('Tipe, Category, dan Target Type line tidak boleh ada yang sama.')
                else:
                    tipe.append(key)
        return create

    def write(self, vals):
        write = super(TwTargetSalesPeople, self).write(vals)
        if self.target_line_ids:
            tipe = []
            for line in self.target_line_ids:
                key = (line.type, line.category_id.id, line.target_type)
                if key in tipe:
                    raise Warning('Tipe, Category, dan Target Type line tidak boleh ada yang sama.')
                else:
                    tipe.append(key)
        return write
    
    # 13: action methods

    # 14: private methods