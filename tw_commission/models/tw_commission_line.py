
# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import math

# 2: import of known third party lib
import xlrd
import base64
from datetime import datetime, timedelta

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwCommissionLine(models.Model):
    _name = "tw.commission.line"
    _description = "Hutang Komisi Line"
    _order = "id asc"
     
    # 7: defaults methods

    # 8: fields
    amount = fields.Float('Amount')
    product_template_id_domain = fields.Binary(compute="_compute_domain_product_type")
    
    # 9: relation fields
    commission_id = fields.Many2one('tw.commission', ondelete='cascade')
    product_template_id = fields.Many2one('product.template', 'Product Template')
    
    # 10: constraints & sql constraints
    _sql_constraints = [
        ('unique_product_hc', 'unique(commission_id,product_template_id)', 'Tidak boleh ada produk yg sama didalam satu master hutang komisi!'),
    ]

    # 11: compute/depends & on change methods
    @api.depends('product_template_id')
    def _compute_domain_product_type(self):
        for record in self:
            categ_ids = self.env['product.category'].get_child_ids('Unit')
            record.product_template_id_domain = [
                ('type', '!=', 'view'),
                ('categ_id', 'in', categ_ids)
            ]

    # 12: override methods

    # 13: action methods

    # 14: private methods
    
    
