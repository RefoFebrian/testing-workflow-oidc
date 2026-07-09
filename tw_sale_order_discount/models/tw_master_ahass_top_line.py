from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class MasterAhassTopLine(models.Model):
    _name = "tw.master.ahass.top.line"
    _description = "Master AHASS TOP Line"

    master_ahass_top_id = fields.Many2one('tw.master.ahass.top','Master AHASS TOP',ondelete='cascade')
    categ_id = fields.Many2one('product.category', 'Category', domain=[('parent_id', 'child_of', 'Sparepart')])
    discount_cash_id = fields.Many2one('tw.sale.discount.cash','Master Discount Cash')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self._check_duplicate_data(vals):
                raise Warning('Detail Master AHASS Top tidak boleh duplikat.')
        return super(MasterAhassTopLine, self).create(vals_list)
    
    def write(self,vals):
        if 'categ_id' in vals or 'discount_cash_id' in vals:
            if self._check_duplicate_data(vals):
                raise Warning('Detail Master AHASS Top tidak boleh duplikat.')
        return super(MasterAhassTopLine, self).write(vals)
    
    def _check_duplicate_data(self, vals):
        domain = [
            ('master_ahass_top_id', '=', vals.get('master_ahass_top_id', self.master_ahass_top_id.id)),
            ('categ_id', '=', vals.get('categ_id', self.categ_id.id)),
            ('discount_cash_id', '=', vals.get('discount_cash_id', self.discount_cash_id.id)),
        ]
        return self.suspend_security().search(domain, limit=1)