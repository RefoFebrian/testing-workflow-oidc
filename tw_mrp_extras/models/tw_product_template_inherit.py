#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class InheritProductTemplate(models.Model):
    _inherit = "product.template"

    # 7: defaults methods
    @api.depends('extras_bom_id', 'extras_bom_id.bom_line_ids')
    def _compute_extras_ids(self):
        """Compute extras components from BoM of type 'extras'."""
        for record in self:
            if record.extras_bom_id:
                record.extras_ids = record.extras_bom_id.bom_line_ids
            else:
                record.extras_ids = self.env['mrp.bom.line']

    @api.depends('extras_bom_id')
    def _compute_default_bom_extras(self):
        for record in self:
            record.default_extras_id = record.extras_bom_id if record.extras_bom_id else False

    def _compute_extras_bom_id(self):
        """Find the BoM of type 'extras' for this product template."""
        MrpBom = self.env['mrp.bom']
        for record in self:
            bom = MrpBom.search([
                ('product_tmpl_id', '=', record.id),
                ('product_id', '=', False),
                ('type', '=', 'extras'),
            ], limit=1)
            if not bom:
                # Also check if there's a variant-specific extras bom
                bom = MrpBom.search([
                    ('product_tmpl_id', '=', record.id),
                    ('type', '=', 'extras'),
                ], limit=1)
            record.extras_bom_id = bom

    def _search_extras_bom_id(self, operator, value):
        """Search method for extras_bom_id field."""
        boms = self.env['mrp.bom'].search([
            ('type', '=', 'extras'),
            ('id', operator, value) if isinstance(value, int) else ('id', '!=', False)
        ])
        return [('id', 'in', boms.mapped('product_tmpl_id').ids)]

    # 8: fields

    # 9: relation fields
    extras_bom_id = fields.Many2one('mrp.bom', string='Extras BoM', compute='_compute_extras_bom_id', search='_search_extras_bom_id')
    default_extras_id = fields.Many2one('mrp.bom', compute="_compute_default_bom_extras", store=False)
    extras_ids = fields.One2many('mrp.bom.line', compute='_compute_extras_ids', string='Extras')
    
    # 10: constraints & sql constraints

    # 10: compute/depends & on change methods

    # 12: override methods   
    def open_extras_tree_menu(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Extras',
            'res_model': 'mrp.bom',
            'view_mode': 'form',
            'context': {
                'default_product_tmpl_id': self.id,
                'default_type': 'extras',
            },
        }
        