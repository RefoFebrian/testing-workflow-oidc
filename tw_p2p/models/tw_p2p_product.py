# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwP2pProduct(models.Model):
    _name = "tw.p2p.product"
    _description ="P2P Product"

    # 7: defaults methods
    
    @api.depends('product_id')
    def _get_division(self):
        for record in self:
            if record.product_id:
                categ_id = record.product_id.categ_id
                division = False
                div = False
                while not div and categ_id:
                    if categ_id.name in ('Unit', 'Sparepart', 'Umum', 'Extras'):
                        div = categ_id.name
                        break
                    elif not categ_id.parent_id:
                        div = categ_id.name
                        break
                    categ_id = categ_id.parent_id
                record.division = div
            else:
                record.division = False

    # 8: fields 
    name = fields.Char(related='product_id.name',string='Name')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    division = fields.Char(string="Division",store=True, readonly=True, compute='_get_division',)
    default_code = fields.Char(related='product_id.default_code',string="Default Code")
    active = fields.Boolean(string='Active', default=True)
    sub_category_name = fields.Char(related='product_id.categ_id.name', string='Sub Category', store=True)

    # 9: relation fields
    product_id = fields.Many2one('product.product', string='Product', required=True, ondelete='restrict')
    categ_id = fields.Many2one(related='product_id.categ_id', string='Category')
    attribute_value_ids = fields.Many2many(related='product_id.product_template_attribute_value_ids')
    company_ids = fields.Many2many(
        'res.company', 
        'tw_p2p_product_company_rel',
        'product_p2p_id',
        'company_id',
        string='Companies', 
        default=lambda self: self._get_default_parent_company(),
        domain="[('parent_id', '=', False)]"  # Only parent companies
    )
    category_fix_order_id = fields.Many2one('tw.p2p.category.fix.order', string='Category Fix Order')

    
    @api.model
    def _get_default_parent_company(self):
        """Get root parent company for default value"""
        company = self.env.company
        while company.parent_id:
            company = company.parent_id
        return company

    # _sql_constraints removed - uniqueness handled via ORM constraint

    @api.constrains('product_id', 'company_ids')
    def _check_unique_product_companies(self):
        for record in self:
            for company in record.company_ids:
                existing = self.search([
                    ('id', '!=', record.id),
                    ('product_id', '=', record.product_id.id),
                    ('company_ids', 'in', company.id)
                ])
                if existing:
                    raise Warning('Product %s sudah pernah dibuat untuk company %s!' % (record.product_id.name, company.name))

    @api.constrains('division', 'category_fix_order_id')
    def _check_category_fix_order_required(self):
        """Category Fix Order is required for Sparepart division"""
        for record in self:
            if record.division == 'Sparepart' and not record.category_fix_order_id:
                raise Warning('Category Fix Order wajib diisi untuk divisi Sparepart!')

    # 11: compute/depends & on change methods
    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date :
            if self.end_date < self.start_date :
                self.end_date = False                  
                raise Warning("End Date tidak boleh kurang dari Start Date ! ")
    
    @api.onchange('active')
    def onchange_active(self):
        today = fields.Date.today()
        if self.active == False:
            if not self.active and self.start_date and self.end_date:
                self.end_date = today - timedelta(days=1)
            elif self.start_date and self.end_date:
                if self.start_date <= today <= self.end_date:
                    self.active = False

    # 12: override methods
    def unlink(self):
        for record in self:
            if record.active:
                record.active = False
            else:
                raise Warning("Master data tidak dapat dihapus !")
            
        return True

    # 13: action methods

    # 14: private methods