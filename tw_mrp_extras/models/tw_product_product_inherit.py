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


class InheritProductProduct(models.Model):
    _inherit = "product.product"

    # 7: defaults methods
    @api.depends('product_tmpl_id.extras_bom_id', 'product_tmpl_id.extras_bom_id.bom_line_ids', 
                 'extras_bom_id', 'extras_bom_id.bom_line_ids')
    def _compute_extras_ids(self):
        """Compute extras components by combining template + variant extras (gabungan approach).
        
        - Template extras: inherited from product.template, applies to ALL variants
        - Variant extras: specific to this variant only, ADDED to template extras
        - Deduplication: variant extras only added if product_id not already in template extras
        """
        for record in self:
            lines = self.env['mrp.bom.line']
            template_product_ids = set()
            
            # 1. Add template-level extras (base extras for all variants)
            if record.product_tmpl_id.extras_bom_id:
                template_lines = record.product_tmpl_id.extras_bom_id.bom_line_ids
                lines |= template_lines
                template_product_ids = set(template_lines.mapped('product_id').ids)
            
            # 2. Add variant-specific extras (only products NOT already in template)
            if record.extras_bom_id and record.extras_bom_id != record.product_tmpl_id.extras_bom_id:
                for bom_line in record.extras_bom_id.bom_line_ids:
                    if bom_line.product_id.id not in template_product_ids:
                        lines |= bom_line
            
            record.extras_ids = lines

    @api.depends('extras_bom_id')
    def _compute_default_bom_extras(self):
        for record in self:
            record.default_extras_id = record.extras_bom_id if record.extras_bom_id else False

    def _compute_extras_bom_id(self):
        """Find the BoM of type 'extras' for this product variant."""
        MrpBom = self.env['mrp.bom']
        for record in self:
            # First check for variant-specific extras bom
            bom = MrpBom.search([
                ('product_id', '=', record.id),
                ('type', '=', 'extras'),
            ], limit=1)
            if not bom:
                # Fallback to template-level extras bom
                bom = MrpBom.search([
                    ('product_tmpl_id', '=', record.product_tmpl_id.id),
                    ('product_id', '=', False),
                    ('type', '=', 'extras'),
                ], limit=1)
            record.extras_bom_id = bom

    def _search_extras_bom_id(self, operator, value):
        """Search method for extras_bom_id field."""
        boms = self.env['mrp.bom'].search([
            ('type', '=', 'extras'),
            ('id', operator, value) if isinstance(value, int) else ('id', '!=', False)
        ])
        product_ids = boms.mapped('product_id').ids
        tmpl_ids = boms.filtered(lambda b: not b.product_id).mapped('product_tmpl_id').ids
        products = self.search([('product_tmpl_id', 'in', tmpl_ids)])
        return [('id', 'in', list(set(product_ids + products.ids)))]

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
                'default_product_id': self.id,
                'default_product_tmpl_id': self.product_tmpl_id.id,
                'default_type': 'extras',
            },
        }
        