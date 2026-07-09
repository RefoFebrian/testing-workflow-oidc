# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAccountPickingBatchInherit(models.Model):
    _inherit = "stock.picking.batch"
    _description = "Stock Picking Batch"
    
    # 7: defaults methods

    # 8: fields
    pricelist_type_value = fields.Char(string="Pricelist Type Value", related='pricelist_type_id.value')

    # 9: relation fields
    volume = fields.Float(string="Volume",default=0.0)

    # 9: relation fields
    pricelist_type_id = fields.Many2one(
        comodel_name='tw.selection',
        string='Pricelist Type',
        domain=[('type', '=', 'PricelistCategory')],
        help="Pricelist that can be used for supplier cost."
    )
    stock_inbound_id = fields.Many2one(comodel_name='tw.stock.inbound', string="Stock Inbound")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('stock_inbound_id')
    def onchange_stock_inbound(self):
        self.pricelist_type_id = False
        self.volume = 0.0
        if self.stock_inbound_id:
            self.pricelist_type_id = self.stock_inbound_id.pricelist_type_id.id
            self.volume = self.stock_inbound_id.volume
        else:
            # Auto-set pricelist type to 'product' when division is 'Unit'
            if self.division == 'Unit' and not self.pricelist_type_id:
                self.pricelist_type_id = self.env.ref(
                    'tw_pricelist.tw_pricelist_data_category_price_product', False
                )

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _set_stock_inbound_id(self,picking):
        if self.pricelist_type_id:
            picking.suspend_security().write({
                'volume': self.volume,
                'pricelist_type_id': self.pricelist_type_id.id,
            })
        return super(TwAccountPickingBatchInherit,self)._set_stock_inbound_id(picking)

    def _prepare_create_batch_vals(self, picking_ids, picking_type_id):
        vals = super()._prepare_create_batch_vals(picking_ids, picking_type_id)
        if self.stock_inbound_id:
            vals['stock_inbound_id'] = self.stock_inbound_id.id
        if self.pricelist_type_id:
            vals['pricelist_type_id'] = self.pricelist_type_id.id
        if self.volume:
            vals['volume'] = self.volume
        return vals
    