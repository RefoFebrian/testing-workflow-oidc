from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class MasterSaleDiscountItems(models.Model):
    _name = "tw.sale.discount.items"
    _description = "Master Sale Discount Items"

    additional = fields.Float('Additional')
    fix = fields.Float('Fix')
    topup = fields.Float('Topup')
    simpart = fields.Float('Simpart')
    hotline = fields.Float('Hotline')
    active = fields.Boolean('Active', default=True)

    categ_id = fields.Many2one('product.category', 'Category', domain=[('parent_id', 'child_of', 'Sparepart')])
    product_id = fields.Many2one('product.product', string='Product')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.categ_id = self.product_id.product_tmpl_id.categ_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('categ_id'):
                product_id = vals['product_id'] if vals.get('product_id') else False
                master_disc_obj = self.search([('categ_id','=',vals['categ_id']),('product_id','=',product_id)])
                if master_disc_obj:
                    if product_id:
                        error = 'Data Master Discount untuk Category : %s dan Product : %s Sudah Terbentuk!' % (master_disc_obj.categ_id.name,master_disc_obj.product_id.product_tmpl_id.name)
                    else:
                        error = 'Data Master Discount untuk Category : %s Sudah Terbentuk!' % (master_disc_obj.categ_id.name)
                    raise Warning(error)
        create = super(MasterSaleDiscountItems,self).create(vals)
        return create

    def write(self,vals):
        if vals.get('categ_id') or vals.get('product_id'):
            product_id = vals['product_id'] if vals.get('product_id') else False
            categ_id = vals['categ_id'] if vals.get('categ_id') else self.categ_id.id
            master_disc_obj = self.search([('categ_id','=',categ_id),('product_id','=',product_id)])
            if master_disc_obj:
                if product_id:
                    error = 'Data Master Discount untuk Category : %s dan Product : %s Sudah Terbentuk!' % (master_disc_obj.categ_id.name,master_disc_obj.product_id.product_tmpl_id.name)
                else:
                    error = 'Data Master Discount untuk Category : %s Sudah Terbentuk!' % (master_disc_obj.categ_id.name)
                raise Warning(error)
        return super(MasterSaleDiscountItems,self).write(vals)

    def unlink(self):
        for record in self:
            record.suspend_security().write({'active':False})
        