# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockLotAccountMove(models.Model):
    _inherit = "stock.lot"
    
    # 7: defaults methods

    # 8: fields
    factur_number = fields.Char(string='Factur Number', help='Factur Number of Vehicle')
    stnk_invoice_price = fields.Float(string='STNK Invoice Price', digits='Product Price', help='Price of STNK Invoice')
    cogs = fields.Float(string='COGS', digits='Product Price', help='Cost of Goods Sold (HPP)', compute='_compute_stock_valuation', compute_sudo=True, store=True)
    initial_cogs = fields.Float(string='Initial COGS', digits='Product Price', help='Also known as Performance HPP', compute='_compute_stock_valuation', compute_sudo=True, store=True)
    stock_valuation = fields.Float(string='Stock Valuation', digits='Product Price', help='Valuation of Stock', company_dependent=True, compute='_compute_stock_valuation', compute_sudo=True, store=True)


    # 9: relation fields
    supplier_invoice_id = fields.Many2one(comodel_name='account.move', string='Supplier Invoice', help='Supplier Invoice of Vehicle')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('stock_valuation_layer_ids','initial_company_id','company_id')
    def _compute_stock_valuation(self):
        for lot in self:
            domain = [
                *self.env['stock.valuation.layer']._check_company_domain(lot.company_id),
                ('lot_id', '=', lot.id),
            ]
            if self.env.context.get('to_date'):
                to_date = fields.Datetime.to_datetime(self.env.context['to_date'])
                domain.append(('create_date', '<=', to_date))
            groups = self.env['stock.valuation.layer']._read_group(
                domain,
                groupby=['lot_id'],
                aggregates=['value:sum', 'quantity:sum'],
            )
            # Browse all lots and compute lots' quantities_dict in batch.
            group_mapping = {lot: aggregates for lot, *aggregates in groups}
        
            value_sum, quantity_sum = group_mapping.get(lot._origin, (0, 0))
            currency = lot.company_currency_id or lot.company_id.currency_id
            value_svl = currency.round(value_sum)
            avg_cost = value_svl / quantity_sum if quantity_sum else 0
            total_value = avg_cost * quantity_sum
            if total_value > 0:
                if lot.state == 'stock':
                    lot.with_company(lot.company_id).stock_valuation = total_value
                if lot.initial_company_id:
                    lot.cogs = total_value
                    if lot.initial_company_id == lot.company_id:
                        lot.initial_cogs = total_value
                    if lot.initial_company_id != lot.company_id:
                        lot.initial_cogs = lot.initial_cogs

    # 12: override methods

    # 13: action methods

    # 14: private methods
    
