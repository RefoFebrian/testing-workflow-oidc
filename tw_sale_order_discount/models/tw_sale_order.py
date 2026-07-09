# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError

class TWSaleOrder(models.Model):
    _inherit = "tw.sale.order"
    
    # Fields
    discount_ids = fields.One2many(
        'tw.sale.order.discount', 
        'sale_order_id', 
        string='Discounts', 
        copy=False, 
        store=True,
        readonly=False,
        compute='_compute_discount_line',
    )
    
    has_discounts = fields.Boolean(
        compute='_compute_has_discounts', 
        store=True, 
        default=False
    )
    
    account_discount_ids = fields.Many2many(
        'tw.account.discount', 
        compute='_compute_account_discount', 
        string='Available Discounts', 
        help='Discounts available for this sale order'
    )

    # Compute methods
    @api.depends('discount_ids.amount')
    def _compute_has_discounts(self):
        """Compute if the order has any discounts with amount > 0"""
        for order in self:
            order.has_discounts = bool(order.discount_ids.filtered(lambda d: d.amount > 0))

    @api.depends('account_discount_ids')
    def _compute_discount_line(self):
        for record in self:
            record.discount_ids = [Command.clear()]
            if record.account_discount_ids:
                discount_ids = []
                for d in record.account_discount_ids:
                    discount_ids.append(Command.create({
                        'name': d.name,
                        'amount': 0,
                        'company_id': record.company_id.id,
                        'currency_id': record.currency_id.id,
                        'discount_id': d.id,
                        'account_id': d.account_id.id,
                        'tax_ids': [Command.set(d.tax_ids.ids)],
                    }))
                record.discount_ids = discount_ids
    
    
    def _get_applicable_discounts_domain(self):
        """
        Get domain to filter applicable discounts for the current order
        :return: domain list for tw.account.discount
        """
        return [
            ('type', '=', 'out_receipt'),
            '|',
            ('is_all_branch', '=', True),
            ('company_ids', 'in', self.company_id.id)
        ]
        
    def _get_applicable_discounts(self):
        """
        Get all applicable discounts for the current order
        :return: recordset of tw.account.discount
        """
        self.ensure_one()
        domain = self._get_applicable_discounts_domain()
        return self.env['tw.account.discount'].sudo().search(domain)

    @api.depends('company_id', 'partner_id')
    def _compute_account_discount(self):
        """Compute available discounts for the current company and branch"""
        for order in self:
            order.account_discount_ids = order._get_applicable_discounts()

    def _prepare_discount_base_lines(self, base_lines):
        """Prepare negative base lines for each discount using the discount's own tax settings.
        
        Instead of adjusting order line prices by a ratio (which uses order line taxes),
        this creates separate negative base lines with the discount's own tax_ids from
        the master discount configuration.
        
        Args:
            base_lines: List of base line dicts from order lines (used to calculate base amount)
            
        Returns:
            list: Negative base line dicts for each discount with amount > 0
        """
        self.ensure_one()
        AccountTax = self.env['account.tax']
        discount_base_lines = []
        
        amount_untaxed = sum(
            line['price_unit'] * line['quantity'] * (1 - line.get('discount', 0) / 100.0)
            for line in base_lines
        )
        
        for discount in self.discount_ids:
            try:
                discount_amount = discount.get_discount_amount(amount_untaxed)
            except UserError as e:
                raise UserError(_("Error calculating discount %s: %s") % (discount.name, str(e)))
            
            if not discount_amount:
                continue
            
            # Use the discount's own tax_ids directly from master (not via related field,
            # which may not resolve for NewId records during onchange)
            discount_tax_ids = discount.discount_id.tax_ids or self.env['account.tax']
            
            # Create a negative base line with the discount's own taxes
            discount_base_line = AccountTax._prepare_base_line_for_taxes_computation(
                discount,
                **{
                    'tax_ids': discount_tax_ids,
                    'price_unit': -discount_amount,
                    'quantity': 1.0,
                    'discount': 0.0,
                    'product_id': self.env['product.product'],
                    'product_uom_id': self.env['uom.uom'],
                    'partner_id': self.partner_id,
                    'currency_id': self.currency_id or self.company_id.currency_id,
                    'rate': self.currency_rate,
                    'is_refund': False,
                    'account_id': discount.discount_id.account_id or self.env['account.account'],
                }
            )
            discount_base_lines.append(discount_base_line)
        
        return discount_base_lines

    @api.depends(
        'order_line.price_subtotal', 'currency_id', 'company_id', 'payment_term_id',
        'discount_ids.amount', 'discount_ids.discount_type',
        'order_line.tax_id', 'order_line.price_unit', 'order_line.product_uom_qty'
    )
    def _compute_amounts(self):
        """Override to include global discounts in order totals.
        
        Discounts are added as negative base lines with their own tax settings
        from the master discount configuration, ensuring proper tax computation.
        """
        AccountTax = self.env['account.tax']
        for order in self:
            # Get base lines for tax computation
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            
            # Add early payment discount lines if any
            base_lines += order._add_base_lines_for_early_payment_discount()
            
            # Add discount as negative base lines with their own taxes
            if order.discount_ids:
                base_lines += order._prepare_discount_base_lines(base_lines)
            
            # Compute taxes with the standard Odoo method
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            
            # Get tax totals
            tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )
            
            # Update order amounts
            order.amount_untaxed = tax_totals['base_amount_currency']
            order.amount_tax = tax_totals['tax_amount_currency']
            order.amount_total = tax_totals['total_amount_currency']
            
        return True
        
    @api.depends_context('lang')
    @api.depends('order_line.price_subtotal', 'currency_id', 'company_id', 'payment_term_id', 'discount_ids.amount')
    def _compute_tax_totals(self):
        """Override to include discounts in tax totals calculation.
        
        Discounts are added as negative base lines with their own tax settings,
        so the tax computation uses the correct tax rates from the master discount.
        """
        AccountTax = self.env['account.tax']
        for order in self:
            # If no discounts with amount, use parent's implementation
            has_discount = any(d.amount > 0 for d in order.discount_ids)
            if not has_discount:
                return super()._compute_tax_totals()
            
            # Prepare base lines for tax computation
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            
            # Add early payment discount lines if any
            if hasattr(order, '_add_base_lines_for_early_payment_discount'):
                base_lines += order._add_base_lines_for_early_payment_discount()
            
            # Add discount as negative base lines with their own taxes
            base_lines += order._prepare_discount_base_lines(base_lines)
            
            # Add tax details to base lines
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            
            # Calculate tax totals
            order.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )
        
        return {}
    
    def _prepare_invoice(self):
        """Prepare invoice values with discount information"""
        invoice_vals = super()._prepare_invoice()
        # Calculate total amount before discount for percentage calculation
        amount_untaxed = sum(line.price_subtotal for line in self.order_line 
                           if not line.display_type)
        
        for discount in self.discount_ids:
            # Calculate the actual discount amount based on type
            if discount.discount_type == 'percentage':
                discount_amount = (amount_untaxed * discount.amount) / 100.0
            else:
                discount_amount = discount.amount
            
            if discount_amount:
                # Prepare discount entry (debit) only for non-zero amounts
                invoice_vals['line_ids'].append((0, 0, {
                    'name': discount.name or 'Discount',
                    'account_id': discount.account_id.id,
                    'debit': discount_amount,
                    'credit': 0.0,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.currency_id.id,
                }))
            # Always add to discount_line_ids for reference (even if amount is 0)
            invoice_vals.setdefault('discount_line_ids', []).append((0, 0, {
                'discount_id': discount.discount_id.id,
                'amount': discount_amount,
                'account_id': discount.account_id.id,
                'tax_ids': [(6, 0, discount.tax_ids.ids)],
            }))
        return invoice_vals
        
    def _check_and_add_new_discounts(self):
        """
        Check for new discount types in master and add them to the order
        This method is called when the order is opened for editing
        """
        self.ensure_one()
        
        # Skip if order is not in draft/sent state
        if self.state not in ['draft', 'sent']:
            return False
            
        # Get all available discount types
        available_discounts = self._get_applicable_discounts()
        
        # Get existing discount types in this order
        existing_discounts = self.discount_ids.mapped('discount_id')
        
        # Find new discounts that are not yet in the order
        new_discounts = available_discounts - existing_discounts
        
        # Add new discounts to the order with 0 amount
        for discount in new_discounts:
            self.write({
                'discount_ids': [(0, 0, {
                    'discount_id': discount.id,
                    'amount': 0.0,
                    'name': discount.display_name or discount.name,  # Use display_name from tw.account.discount
                    'account_id': discount.account_id.id,
                    'tax_ids': [(6, 0, discount.tax_ids.ids)],
                    'company_id': self.company_id.id,
                    'currency_id': self.currency_id.id,
                })]
            })
        
        return bool(new_discounts)  # Return True if new discounts were added
        
    def action_update_discounts(self):
        """
        Action to manually check and add new discount types
        Can be called from a button in the form view
        """
        self.ensure_one()
        
        # Only allow for draft/sent orders
        if self.state not in ['draft', 'sent']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _('Discounts can only be updated for draft or sent orders.'),
                    'sticky': False,
                }
            }
            
        updated = self._check_and_add_new_discounts()
        
        if updated:
            # Reload the form if there are new discounts
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {
                    'type': 'success',
                    'message': _('New discount types have been added to this order.'),
                    'sticky': False,
                }
            }
        else:
            # Just show info message if no new discounts
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': _('No new discount types found.'),
                    'sticky': True,
                }
            }
