from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class B2bFileStockMove(models.Model):
    _inherit = "stock.move"
    _description = "Stock Move"

    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        for record in self:
            picking_ids = record.move_orig_ids.picking_id.ids
            if not picking_ids:
                continue

            picking_obj = self.env['stock.picking'].suspend_security().search([
                ('id', 'in', picking_ids),
                ('mft_reference', '!=', False),
            ], limit=1)
            if picking_obj:
                res.update({
                    'mft_reference': picking_obj.mft_reference,
                })

        return res
