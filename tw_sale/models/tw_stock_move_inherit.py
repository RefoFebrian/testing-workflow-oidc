# 1: imports of python lib
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

class SaleStockMove(models.Model):
    _inherit = "stock.move"

    sale_order_line_id = fields.Many2one('tw.sale.order.line', 'SO Lines', index='btree_not_null')

    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        for record in self:
            model_name = self.env.context.get('model_name')
            if model_name and record.sale_order_line_id:
                sale_order_obj = self.env[model_name].suspend_security().search([('name','=',record.origin)])
                if sale_order_obj:
                    res.update({
                        'division': sale_order_obj.division,
                        'company_id': sale_order_obj.company_id.id,
                        'partner_id': sale_order_obj.partner_id.id,
                    })
        return res
    
    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(SaleStockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('sale_order_line_id')
        return distinct_fields
    
    def _get_sale_order_lines(self):
        """ Return all possible sale order lines for one stock move. """
        self.ensure_one()
        return (self + self.browse(self._rollup_move_origs() | self._rollup_move_dests())).sale_order_line_id
    
    def _get_all_related_sm(self, product):
        return super()._get_all_related_sm(product) | self.filtered(lambda m: m.sale_order_line_id.product_id == product)

    def _should_skip_serial_auto_assign(self):
        """
        Check if serial auto-assignment should be skipped for this move.
        
        Returns True for moves belonging to mutation order / sale order pickings.
        Can be extended to add more conditions.
        """
        is_skip = super()._should_skip_serial_auto_assign()
        if self.picking_id and self.picking_id.sale_order_id and self._is_first_move_from_route():
            is_skip = True
        return is_skip