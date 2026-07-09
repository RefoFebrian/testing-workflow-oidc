# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero
from collections import defaultdict
from odoo.fields import Command

class TwPurchaseReturnLine(models.Model):
    _name = "tw.purchase.return.line"
    _inherit = "sale.order.line"
    _description = "Purchase Return Line"
    _order = "order_id"
    
    return_description = fields.Text('Return Details')
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0, store=True, readonly=False, compute='_compute_price_unit', compute_sudo=True)
    
    order_id = fields.Many2one('tw.purchase.return', string='Return Reference', required=True, ondelete='cascade', index=True, copy=False)
    purchase_line_id = fields.Many2one('purchase.order.line', string='Original Purchase Line', ondelete='set null', copy=False, index=True)
    
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial', ondelete='set null', copy=False, index=True)
    invoice_lines = fields.Many2many(comodel_name='account.move.line',relation='tw_purchase_return_line_invoice_rel', column1='order_line_id', column2='invoice_line_id',string="Invoice Lines",copy=False)
    product_document_ids = fields.Many2many(string="Product Documents",
        help="The product documents for this order line that will be merged in the PDF quote.",
        comodel_name='product.document',
        relation='tw_purchase_return_line_product_document_rel',
        readonly=False,
        domain="[('id', 'in', available_product_document_ids)]",
    )
    move_ids = fields.One2many('stock.move', 'purchase_return_line_id', string='Stock Moves')

    @api.depends('product_id', 'company_id')
    def _compute_tax_id(self):
        lines_by_company = defaultdict(lambda: self.env['tw.purchase.return.line'])
        cached_taxes = {}
        for line in self:
            if line.product_type == 'combo':
                line.tax_id = False
                continue
            lines_by_company[line.company_id] += line
        for company, lines in lines_by_company.items():
            for line in lines.with_company(company):
                taxes = None
                if line.product_id:
                    taxes = line.product_id.taxes_id._filter_taxes_by_company(company)
                if not line.product_id or not taxes:
                    # Nothing to map
                    line.tax_id = False
                    continue
                fiscal_position = line.order_id.fiscal_position_id
                cache_key = (fiscal_position.id, company.id, tuple(taxes.ids))
                cache_key += line._get_custom_compute_tax_cache_key()
                if cache_key in cached_taxes:
                    result = cached_taxes[cache_key]
                else:
                    result = fiscal_position.map_tax(taxes)
                    cached_taxes[cache_key] = result
                # If company_id is set, always filter taxes by the company
                line.tax_id = result


    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Update UoM, lot domain, and unit price when product changes
        """
        if not self.product_id:
            return

        # Set default taxes
        self.tax_id = self.product_id.supplier_taxes_id.filtered(
            lambda t: t.company_id == self.order_id.company_id
        )
        
        # Set price unit from PO invoice line if available
        if self.order_id.invoice_id and self.product_id:
            invoice_line = self.order_id.invoice_id.invoice_line_ids.filtered(
                lambda l: l.product_id == self.product_id
            )
            if invoice_line and len(invoice_line) == 1:
                self.price_unit = invoice_line[0].price_unit
        
    
    @api.onchange('quantity')
    def _onchange_quantity(self):
        """
        Validate quantity
        """
        if self.quantity < 0:
            raise UserError(_('Quantity cannot be negative'))
    
    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        """
        Validate unit price
        """
        if self.price_unit < 0:
            raise UserError(_('Unit price cannot be negative'))
    
    @api.constrains('quantity')
    def _check_quantity(self):
        """
        Check if quantity is positive
        """
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than 0'))
    
    def write(self, values):
        lines = self.env['tw.purchase.return.line']
        if 'product_uom_qty' in values:
            lines = self.filtered(lambda r: r.state == 'sale' and not r.is_expense)

        if 'product_packaging_id' in values:
            self.move_ids.filtered(
                lambda m: m.state not in ['cancel', 'done']
            ).product_packaging_id = values['product_packaging_id']

        previous_product_uom_qty = {line.id: line.product_uom_qty for line in lines}
        res = super().write(values)
        if lines:
            lines._action_launch_stock_rule(previous_product_uom_qty)
        return res
    

    def _prepare_invoice_line(self, **optional_values):
        invoice_line = super()._prepare_invoice_line(**optional_values)
        invoice_line.pop('sale_line_ids')
        invoice_line.update({
            'company_id': self.order_id.company_id.id,
            'division': self.order_id.division,
            'purchase_return_line_ids': [Command.link(self.id)],
        })
        return invoice_line
    
    def _prepare_procurement_values(self, group_id=False):
        """
        Prepare procurement values for creating stock moves.
        Adds restrict_lot_ids based on the lot_id selected in the line.
        """
        values = super()._prepare_procurement_values(group_id)
        self.ensure_one()
        if values.get('sale_line_id'):
            values.pop('sale_line_id')

        values.update({'purchase_return_line_id': self.id})
        
        # Add restrict_lot_ids from lot_id selected in line
        if self.lot_id:
            values.update({'restrict_lot_ids': [(6, 0, [self.lot_id.id])]})
        
        return values
    
    def _prepare_procurement_group_vals(self):
        vals = super()._prepare_procurement_group_vals()
        if vals.get('sale_id'):
            vals.pop('sale_id')
        return {
            'name': self.order_id.name,
            'move_type': self.order_id.picking_policy,
            'purchase_return_id': self.order_id.id,
            'partner_id': self.order_id.partner_shipping_id.id,
        }
