# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, Command,fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.osv.expression import AND

# 5: local imports

# 6: Import of unknown third party lib

class InheritMrpBom(models.Model):
    _inherit = "mrp.bom"

    # 7: defaults methods

    # 8: fields
    type = fields.Selection(selection_add=[
        ('extras', 'Extras')
    ],ondelete={'extras': 'set default'})
    product_origin_id = fields.Many2one('product.template', string='Product Origin', help='Produk awal sebelum dijadikan produk bundling')
    bom_origin_id = fields.Many2one('mrp.bom', string='BoM Origin', help='BoM untuk produk awal sebelum dijadikan produk bundling')

    # 9: relation fields

    # 10: constraints & sql constraints
    @api.constrains('type', 'company_id')
    def _check_extras_company_required(self):
        """Validate that company_id is mandatory for extras type BOM."""
        for record in self:
            if record.type == 'extras' and not record.company_id:
                raise Warning("Field Branch wajib diisi untuk BOM dengan tipe Extras!")

    # 11: compute/depends & on change methods
    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id_check_origin(self):
        if self.product_tmpl_id:
            self.product_origin_id = self.product_tmpl_id.product_origin_id.id
        else:
            self.product_origin_id = False
    
    @api.onchange('product_origin_id')
    def _onchange_product_origin_id(self):
        origin_extras = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_origin_id.id),
            ('type', '=', 'extras'),
            '|',
            ('company_id', '=', self.company_id.id),
            ('company_id', '=', self.company_id.parent_id.id)
            ], limit=1)
        if origin_extras:
            self.bom_origin_id = origin_extras.id
            for bom_line in origin_extras.bom_line_ids:
                self.bom_line_ids = [Command.create({
                    'product_id': bom_line.product_id.id,
                    'product_tmpl_id': bom_line.product_tmpl_id.id,
                    'product_qty': bom_line.product_qty,
                    'product_uom_id': bom_line.product_uom_id.id,
                    'sequence': bom_line.sequence,
                    'type': bom_line.type,
                })]
        else:
            self.bom_origin_id = False
            
    # 12: override methods
    @api.model
    def _bom_find_domain(self, products, picking_type=None, company_id=False, bom_type=False):
        """Override to support company hierarchy for extras BOM type.

        When bom_type is 'extras', replace exact company match with
        hierarchy-aware filter using parent_of operator.
        """
        if bom_type == 'extras' and company_id:
            # Build domain without company filter first
            domain = super()._bom_find_domain(
                products, picking_type=picking_type,
                company_id=False, bom_type=bom_type,
            )
            # Add company hierarchy filter using parent_of
            domain = AND([domain, [('company_id', 'parent_of', company_id)]])
            return domain
        return super()._bom_find_domain(
            products, picking_type=picking_type,
            company_id=company_id, bom_type=bom_type,
        )

    @api.model_create_multi
    def create(self,vals_list):
        create = super().create(vals_list)
        for extras in create:
            if extras.type == "extras":
                extras._check_product()
        return create
    
    def write(self,vals):
        write = super().write(vals)
        if self.type == "extras":
            self._check_product()
        return write

    # 13: action methods

    # 14: private methods


    def _check_product(self):
        """
        Check for duplicate extras BOM within the same company only.
        
        Validates that no duplicate BOM exists for the same product within
        the same company. This allows child companies to override parent's
        extras master with their own configuration.
        """
        self.ensure_one()
        product_id = self.product_id.id
        product_tmpl_id = self.product_tmpl_id.id
        company_id = self.company_id
        company_name = company_id.name if company_id else 'tanpa Branch'

        # Check if product variant already exists in the same company
        if product_id:
            duplicate = self.search([
                ('id', '!=', self.id),
                ('company_id', '=', company_id.id),
                ('product_id', '=', product_id),
                ('type', '=', 'extras')
            ], limit=1)
            if duplicate:
                raise Warning(
                    "Product Variant %s sudah ada pada master Extras di branch %s" 
                    % (duplicate.product_id.display_name, company_name)
                )
        
        # Check if product template already exists in the same company
        elif product_tmpl_id:
            duplicate = self.search([
                ('id', '!=', self.id),
                ('company_id', '=', company_id.id),
                ('product_id', '=', False),
                ('product_tmpl_id', '=', product_tmpl_id),
                ('type', '=', 'extras')
            ], limit=1)
            if duplicate:
                raise Warning(
                    "Product %s sudah ada pada master Extras di branch %s" 
                    % (duplicate.product_tmpl_id.display_name, company_name)
                )
            
            if self.product_origin_id:
                origin_extras = self.env['mrp.bom'].search([
                    ('product_tmpl_id', '=', self.product_origin_id.id),
                    ('type', '=', 'extras'),
                    '|',
                    ('company_id', '=', self.company_id.id),
                    ('company_id', '=', self.company_id.parent_id.id)
                    ], limit=1)
                if origin_extras:
                    origin_bom_line = origin_extras.bom_line_ids
                    bom_line_ids = origin_bom_line.mapped('product_tmpl_id') - self.bom_line_ids.mapped('product_tmpl_id')
                    if bom_line_ids:
                        names = ', '.join(bom_line_ids.mapped('display_name'))
                        raise Warning("Product %s yang berada di %s seharusnya ada juga sebagai komponen di master Extras %s" % (names, self.product_origin_id.display_name, self.product_tmpl_id.display_name))

        
