# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    dealer_sale_order_line_ids = fields.Many2many(
        'tw.dealer.sale.order.line',
        'tw_dealer_sale_order_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='Dealer Dealer Sales Order Lines', readonly=True, copy=False)

    def _stock_account_get_anglo_saxon_price_unit(self):
        """Override to use lot-specific SVL value for accurate COGS pricing.

        When the invoice line is linked to a dealer sale order line that has a lot_id,
        the COGS price is taken from that lot's stock valuation layer instead of
        the product-level average/standard price.
        """
        price_unit = super()._stock_account_get_anglo_saxon_price_unit()

        dso_line = self.dealer_sale_order_line_ids[:1]
        if not dso_line or not dso_line.lot_id:
            return price_unit
        
        if dso_line.product_id.id != self.product_id.id:
            return price_unit

        lot = dso_line.lot_id.with_company(self.company_id)
        lot_price = self._get_lot_valuation_price(lot, dso_line)

        if self.product_uom_id and self.product_id.uom_id != self.product_uom_id:
            lot_price = self.product_id.uom_id._compute_price(lot_price, self.product_uom_id)

        return lot_price

    def _get_lot_valuation_price(self, lot, dso_line):
        """Get the valuation price from a lot's SVL, with fallbacks.

        Priority:
        1. force_cogs from dealer sale order line (if set)
        2. lot's SVL value (value_svl / quantity_svl)
        3. lot's standard_price
        4. product's standard_price
        """
        if dso_line.price_unit_purchase:
            return dso_line.price_unit_purchase
        
        lot = lot.with_company(self.company_id)
        if lot.quantity_svl:
            return lot.value_svl / lot.quantity_svl

        return lot.standard_price or self.product_id.with_company(self.company_id).standard_price

    def _copy_data_extend_business_fields(self, values):
        # OVERRIDE to copy the 'dealer_sale_order_line_ids' field as well.
        super()._copy_data_extend_business_fields(values)
        values['dealer_sale_order_line_ids'] = [(6, None, self.dealer_sale_order_line_ids.ids)]

    def _sale_can_be_reinvoice(self):
        """ determine if the generated analytic line should be reinvoiced or not.
            For Vendor Bill flow, if the product has a 'erinvoice policy' and is a cost, then we will find the SO on which reinvoice the AAL
        """
        self.ensure_one()
        if self.dealer_sale_order_line_ids:
            return False
        return super()._sale_can_be_reinvoice()

    def _sale_create_reinvoice_sale_line(self):

        sale_order_map = self._sale_determine_order()

        sale_line_values_to_create = []  # the list of creation values of sale line to create.
        existing_sale_line_cache = {}  # in the sales_price-delivery case, we can reuse the same sale line. This cache will avoid doing a search each time the case happen
        # `map_move_sale_line` is map where
        #   - key is the move line identifier
        #   - value is either a tw.dealer.sale.order.line record (existing case), or an integer representing the index of the sale line to create in
        #     the `sale_line_values_to_create` (not existing case, which will happen more often than the first one).
        map_move_sale_line = {}

        for move_line in self:
            sale_order = sale_order_map.get(move_line.id)

            # no reinvoice as no sales order was found
            if not sale_order:
                continue

            # raise if the sale order is not currently open
            if sale_order.state in ('draft', 'sent'):
                raise Warning(_(
                    "Dealer Sales Order %(order)s yang akan di re-invoiced harus sudah divalidasi sebelum mendaftarkan biaya.",
                    order=sale_order.name,
                ))
            elif sale_order.state == 'cancel':
                raise Warning(_(
                    "Dealer Sales Order %(order)s yang akan di re-invoiced sudah dibatalkan."
                    " Anda tidak dapat mendaftarkan biaya pada Dealer Sales Order yang sudah dibatalkan.",
                    order=sale_order.name,
                ))
            elif sale_order.locked:
                raise Warning(_(
                    "Dealer Sales Order %(order)s yang akan di re-invoiced sedang terkunci."
                    " Anda tidak dapat mendaftarkan biaya pada Dealer Sales Order yang terkunci.",
                    order=sale_order.name,
                ))

            price = move_line._sale_get_invoice_price(sale_order)

            # find the existing sale.line or keep its creation values to process this in batch
            sale_line = None
            if (
                move_line.product_id.expense_policy == 'sales_price'
                and move_line.product_id.invoice_policy == 'delivery'
                and not self.env.context.get('force_split_lines')
            ):
                # for those case only, we can try to reuse one
                map_entry_key = (sale_order.id, move_line.product_id.id, price)  # cache entry to limit the call to search
                sale_line = existing_sale_line_cache.get(map_entry_key)
                if sale_line:  # already search, so reuse it. sale_line can be tw.dealer.sale.order.line record or index of a "to create values" in `sale_line_values_to_create`
                    map_move_sale_line[move_line.id] = sale_line
                    existing_sale_line_cache[map_entry_key] = sale_line
                else:  # search for existing sale line
                    sale_line = self.env['tw.dealer.sale.order.line'].search([
                        ('order_id', '=', sale_order.id),
                        ('price_unit', '=', price),
                        ('product_id', '=', move_line.product_id.id),
                        ('is_expense', '=', True),
                    ], limit=1)
                    if sale_line:  # found existing one, so keep the browse record
                        map_move_sale_line[move_line.id] = existing_sale_line_cache[map_entry_key] = sale_line
                    else:  # should be create, so use the index of creation values instead of browse record
                        # save value to create it
                        sale_line_values_to_create.append(move_line._dealer_sale_prepare_sale_line_values(sale_order, price))
                        # store it in the cache of existing ones
                        existing_sale_line_cache[map_entry_key] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line
                        # store it in the map_move_sale_line map
                        map_move_sale_line[move_line.id] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line

            else:  # save its value to create it anyway
                sale_line_values_to_create.append(move_line._dealer_sale_prepare_sale_line_values(sale_order, price))
                map_move_sale_line[move_line.id] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line

        # create the sale lines in batch
        new_sale_lines = self.env['tw.dealer.sale.order.line'].create(sale_line_values_to_create)

        # build result map by replacing index with newly created record of tw.dealer.sale.order.line
        result = {}
        for move_line_id, unknown_sale_line in map_move_sale_line.items():
            if isinstance(unknown_sale_line, int):  # index of newly created sale line
                result[move_line_id] = new_sale_lines[unknown_sale_line]
            elif isinstance(unknown_sale_line, models.BaseModel):  # already record of tw.dealer.sale.order.line
                result[move_line_id] = unknown_sale_line
        return result

    def _dealer_sale_prepare_sale_line_values(self, order, price):
        """ Generate the sale.line creation value from the current move line """
        self.ensure_one()
        last_so_line = self.env['tw.dealer.sale.order.line'].search([('order_id', '=', order.id)], order='sequence desc', limit=1)
        last_sequence = last_so_line.sequence + 1 if last_so_line else 100
        
        fpos = order.fiscal_position_id or order.fiscal_position_id._get_fiscal_position(order.partner_id)
        product_taxes = self.product_id.taxes_id._filter_taxes_by_company(order.company_id)
        taxes = fpos.map_tax(product_taxes)

        return {
            'order_id': order.id,
            'name': self.name,
            'sequence': last_sequence,
            'price_unit': price,
            'tax_id': [x.id for x in taxes],
            'discount': 0.0,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.quantity,
            'is_expense': True,
        }

    def _get_downpayment_lines(self):
        if self.dealer_sale_order_line_ids:
        # OVERRIDE
            return self.dealer_sale_order_line_ids.filtered('is_downpayment').invoice_lines.filtered(lambda line: line.move_id._is_downpayment())
        return super()._get_downpayment_lines()
