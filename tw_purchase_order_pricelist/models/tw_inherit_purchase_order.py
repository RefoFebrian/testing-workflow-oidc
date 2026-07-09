# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import api, fields, models, _

from odoo.exceptions import UserError as Warning

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritPurchaseOrderPricelist(models.Model):
    _inherit = "purchase.order"

    # 7: defaults methods
    
    # 8: fields 
    pricelist_id = fields.Many2one(comodel_name='product.pricelist',string="Pricelist",compute='_compute_pricelist_id',store=True, readonly=False, precompute=True, check_company=True, tracking=1,domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",help="If you change the pricelist, only newly added lines will be affected.")
    is_only_use_pricelist = fields.Boolean('Is only use pricelist?', compute='_compute_is_only_use_pricelist')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _compute_is_only_use_pricelist(self):
        is_only_use_pricelist = self.env['ir.config_parameter'].sudo().get_param('tw_pricelist.is_only_use_pricelist') or False
        for record in self:
            record.is_only_use_pricelist = is_only_use_pricelist

    @api.depends('company_id', 'division')
    def _compute_pricelist_id(self):
        for record in self:
            record = record.with_company(record.company_id)
            record.pricelist_id = record._get_pricelist()
    

    # 12 default 
    def copy(self,default=None):
        default = dict(default or {})
        copy = super().copy(default)
        copy._compute_pricelist_id()
        return copy
    
    def _get_pricelist(self):
        return self.env['tw.branch.setting']._get_pricelist_purchase(self.company_id, self.division)
    