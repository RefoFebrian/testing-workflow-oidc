# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, Command,fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritMrpBomLine(models.Model):
    _inherit = "mrp.bom.line"


    # 8: fields
    type = fields.Selection(related='bom_id.type')
    product_domain = fields.Char(compute='_compute_product_domain')

    # 9: relation fields
    product_id = fields.Many2one('product.product', 'Component', check_company=True, required=False)

    # 10: constraints & sql constraints
    @api.constrains('product_id', 'bom_id')
    def _check_unique_product_id(self):
        for rec in self:
            if rec.bom_id and rec.product_id:
                duplicate_lines = rec.bom_id.mapped('bom_line_ids').filtered(lambda x: x.product_id.id == rec.product_id.id and x.id != rec.id)
                if duplicate_lines:
                    raise Warning(_('Duplicate product %s in BoM %s' % (rec.product_id.name, rec.bom_id.display_name)))
    
    # 11: compute/depends & on change methods
    @api.depends('bom_id')
    def _compute_product_domain(self):
        for record in self:
            if record.type == 'extras':
                record.product_domain = [('division','=','Extras')]
            else:
                record.product_domain = [('division','!=','Extras')]

    # 12: override methods
    
    # 13: action methods

    # 14: private methods
    @api.model
    def default_get(self, fields_list):
        res = super(InheritMrpBomLine, self).default_get(fields_list)
        product_id = self.env.context.get('default_product_header_id')

        if product_id:
            product = self.env['product.product'].browse(product_id)
            existing_bom = product.extras_ids.filtered(lambda x: x.bom_id).mapped('bom_id')
            if existing_bom:
                res['bom_id'] = existing_bom[0].id  # Ambil bom_id dari line pertama

        return res
