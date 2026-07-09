from odoo import models, fields, api, _


class SaleOrderStockDistribution(models.Model):
    _inherit = "tw.sale.order"
    # INFO : Override from Sale Order and Connected to Stock Distribution'

    stock_distribution_id = fields.Many2one('tw.stock.distribution', string='Stock Distribution')

    def action_confirm(self):
        qty = {}
        approved_qty = {}
        if self.stock_distribution_id:
            if self.state == 'approved' :
                for dist_line in self.stock_distribution_id.stock_distribution_ids :
                    qty[dist_line.product_id] = qty.get(dist_line.product_id,0) + dist_line.qty
                    approved_qty[dist_line.product_id] = approved_qty.get(dist_line.product_id,0) + dist_line.approved_qty
                    if (approved_qty[dist_line.product_id] - qty[dist_line.product_id]) >= 0 :
                        dist_line.write({ 'qty': qty[dist_line.product_id] })
                    else :
                        raise Warning(f"Attention! The Quantity of Product : {dist_line.product_id.name_template} Exceeds the Approved Quantity.")
            
            if all(dl.approved_qty - dl.qty == 0 for dl in self.stock_distribution_id.stock_distribution_ids):
                self.stock_distribution_id.state = 'done'
            
        return super().action_confirm()