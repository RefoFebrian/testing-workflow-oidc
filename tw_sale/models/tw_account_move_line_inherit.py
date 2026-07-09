from odoo import models, fields, api, _

class SaleAccountMoveLineInherit(models.Model):	
    _inherit = "account.move.line"	

    sale_order_line_ids = fields.Many2many(	
        'tw.sale.order.line',	
        'tw_sale_order_line_invoice_rel',	
        'invoice_line_id', 'order_line_id',	
        string='SO Lines', readonly=True, copy=False)	

    def _stock_account_get_anglo_saxon_price_unit(self):
        """
        Custom: gunakan Unit COGS jika invoice berasal dari Sale Order.
        Fallback ke perilaku standar Odoo jika tidak memenuhi kondisi.
        """
        self.ensure_one()
        price = super()._stock_account_get_anglo_saxon_price_unit()
        # Jika bukan product atau bukan real-time valuation, gunakan default
        if not self.product_id or not self.product_id.is_storable:
            return super()._stock_account_get_anglo_saxon_price_unit()

        # Hanya untuk invoice penjualan
        if self.move_id.move_type not in ('out_invoice', 'out_refund'):
            return super()._stock_account_get_anglo_saxon_price_unit()

        # Ambil sale order line (relasi)
        sale_line = self.sale_order_line_ids[:1]  # ambil satu pertama (biasanya 1:1)
        chosen_unit = None

        if sale_line and getattr(sale_line, 'cogs', False):
            chosen_unit = float(sale_line.cogs)
        
        if chosen_unit is not None:
            return chosen_unit

        # Fallback ke default Odoo behaviour
        return price
