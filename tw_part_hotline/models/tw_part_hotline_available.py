# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class PartHotlineAvailable(models.Model):
    _name = "tw.part.hotline.available"
    _description = "TW Part Hotline Available"

    # 7: defaults methods

    # 8: fields
    name = fields.Char('Location')
    qty = fields.Float('Qty')
    aging = fields.Char('Aging')

    # 9: relation fields
    hotline_id = fields.Many2one('tw.part.hotline','Part Hotline',ondelete='cascade')
    company_id = fields.Many2one('res.company','Branch', domain=[('parent_id','!=',False)])
    product_id = fields.Many2one('product.product','Product')