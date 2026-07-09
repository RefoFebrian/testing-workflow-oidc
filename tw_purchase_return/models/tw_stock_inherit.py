# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class SaleStockMove(models.Model):
    _inherit = "stock.move"
    
    purchase_return_line_id = fields.Many2one('tw.purchase.return.line', 'Purchase Return Line', index='btree_not_null')

    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        for record in self:
            model_name = self.env.context.get('model_name')
            if model_name and record.purchase_return_line_id:
                
                purchase_return_obj = self.env[model_name].suspend_security().search([('name','=',record.origin)])
                if purchase_return_obj:
                    warehouse = purchase_return_obj.warehouse_id
                    picking_type = warehouse.purchase_return_type_id
                    
                    if not picking_type:
                        raise Warning(_('No purchase return picking type configured for warehouse %s') % warehouse.name)
                    if not picking_type.default_location_src_id or not picking_type.default_location_dest_id:
                        raise Warning(_('No default source or destination location configured for purchase return picking type %s') % picking_type.name)

                    res.update({
                        'division': purchase_return_obj.division,
                        'company_id': purchase_return_obj.company_id.id,
                        'partner_id': purchase_return_obj.partner_id.id,
                        'picking_type_id': picking_type.id,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': picking_type.default_location_dest_id.id,
                    })
        return res
    
    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(SaleStockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('purchase_return_line_id')
        return distinct_fields
    
    def _get_purchase_return_lines(self):
        """ Return all possible purchase return lines for one stock move. """
        self.ensure_one()
        return (self + self.browse(self._rollup_move_origs() | self._rollup_move_dests())).purchase_return_line_id
    
    def _get_all_related_sm(self, product):
        return super()._get_all_related_sm(product) | self.filtered(lambda m: m.purchase_return_line_id.product_id == product)
    