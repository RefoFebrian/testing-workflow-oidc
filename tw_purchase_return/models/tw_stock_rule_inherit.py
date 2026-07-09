from odoo import models, fields, api, _


class SaleStockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        """
        Add custom fields to be copied from procurement values to stock.move.
        - purchase_return_line_id: link to the Purchase Return Line
        - restrict_lot_ids: restrict lot selection based on lot_id from line
        """
        fields = super(SaleStockRule, self)._get_custom_move_fields()
        fields += ['purchase_return_line_id', 'restrict_lot_ids']
        return fields