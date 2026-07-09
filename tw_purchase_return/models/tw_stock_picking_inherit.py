# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.tools.sql import column_exists, create_column

class SaleStockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_return_id = fields.Many2one('tw.purchase.return', compute="_compute_purchase_return_id", inverse="_set_purchase_return_id", string="Purchase Returns", store=True, index='btree_not_null')

    @api.depends('group_id')
    def _compute_purchase_return_id(self):
        for picking in self:
            picking.purchase_return_id = picking.group_id.purchase_return_id

    def _set_purchase_return_id(self):
        if self.group_id:
            self.group_id.purchase_return_id = self.purchase_return_id
        else:
            if self.purchase_return_id:
                vals = {
                    'purchase_return_id': self.purchase_return_id.id,
                    'name': self.purchase_return_id.name,
                }
            else:
                vals = {}

            pg = self.env['procurement.group'].create(vals)
            self.group_id = pg

    def _auto_init(self):
        """
        Create related field here, too slow
        when computing it afterwards through _compute_related.

        Since group_id.purchase_return_id is created in this module,
        no need for an UPDATE statement.
        """
        if not column_exists(self.env.cr, 'stock_picking', 'purchase_return_id'):
            create_column(self.env.cr, 'stock_picking', 'purchase_return_id', 'int4')
        return super()._auto_init()

    def _process_validate_picking(self):
        """Override to trigger action_done on Purchase Return when picking is validated."""
        res = super()._process_validate_picking()
        
        # Trigger action_done on Purchase Return when outgoing picking is done
        if self.purchase_return_id and self.picking_type_id.code == 'outgoing':
            self.purchase_return_id.action_done()
        
        return res