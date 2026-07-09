# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.tools.sql import column_exists, create_column

class SaleStockPicking(models.Model):
    _inherit = "stock.picking"

    sale_order_id = fields.Many2one('tw.sale.order', compute="_compute_sale_order_id", inverse="_set_sale_order_id", string="Sales Orders", store=True, index='btree_not_null')

    @api.depends('group_id')
    def _compute_sale_order_id(self):
        for picking in self:
            picking.sale_order_id = picking.group_id.sale_order_id

    def _set_sale_order_id(self):
        if self.group_id:
            self.group_id.sale_order_id = self.sale_order_id
        else:
            if self.sale_order_id:
                vals = {
                    'sale_order_id': self.sale_order_id.id,
                    'name': self.sale_order_id.name,
                }
            else:
                vals = {}

            pg = self.env['procurement.group'].create(vals)
            self.group_id = pg

    def _auto_init(self):
        """
        Create related field here, too slow
        when computing it afterwards through _compute_related.

        Since group_id.sale_order_id is created in this module,
        no need for an UPDATE statement.
        """
        if not column_exists(self.env.cr, 'stock_picking', 'sale_order_id'):
            create_column(self.env.cr, 'stock_picking', 'sale_order_id', 'int4')
        return super()._auto_init()

    def _prepare_update_lot(self, picking, move=False, move_line=False):
        """
        Override to update lot state to 'sold' when Sale Order picking is validated.
        """
        res = super(SaleStockPicking, self)._prepare_update_lot(picking, move, move_line)
        if picking.sale_order_id and move._is_last_move_from_route():
            # Update lot state to 'sold' if not already paid
            if move_line.lot_id.state not in ('paid', 'paid_offtr'):
                res.update({'state': 'sold'})

        return res

    def _process_validate_picking(self):
        """Override to trigger action_done on Sale Order when picking is validated."""
        res = super()._process_validate_picking()
        
        # Trigger action_done on Sale Order when outgoing picking is done
        if self.sale_order_id and self.picking_type_id.code == 'outgoing':
            self.sale_order_id.action_done()
        
        return res