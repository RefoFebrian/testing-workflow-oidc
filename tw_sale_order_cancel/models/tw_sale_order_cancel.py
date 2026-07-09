# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from odoo.fields import Command
from odoo.tools.float_utils import float_compare

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwSaleOrderCancel(models.Model):
    """
    Model untuk pembatalan Sale Order (tw.sale.order).
    Menggunakan pola _inherits ke tw.cancellation untuk mewarisi field dan behavior.
    """
    _name = "tw.sale.order.cancel"
    _description = 'Sale Order Cancel'
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()

    # 8: fields

    # 9: relation fields
    sale_order_id = fields.Many2one('tw.sale.order', 'Sale Order')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')
    allow_cancel_so_with_payment = fields.Boolean(
        related='company_id.branch_setting_id.allow_cancel_so_with_payment',
        string='Allow Cancel SO with Payment',
    )
    paid_sale_order_ids = fields.Many2many(
        'tw.sale.order',
        compute='_compute_paid_sale_order_ids',
        string='Paid Sale Orders',
    )

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('unique_sale_order_id', 'unique(sale_order_id)', 'Sale Order pernah diinput sebelumnya!')
    ]

    # 11: compute/depends & on change methods
    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            self.transaction_name = self.sale_order_id.name
            self.name = "X" + self.sale_order_id.name
            self.division = self.sale_order_id.division
        else:
            self.transaction_name = False
            self.name = False

    @api.depends('company_id', 'allow_cancel_so_with_payment')
    def _compute_paid_sale_order_ids(self):
        """Compute SO IDs that have paid invoices, for domain filtering."""
        for record in self:
            if record.allow_cancel_so_with_payment:
                record.paid_sale_order_ids = False
            else:
                paid_so = self.env['tw.sale.order'].search([
                    ('company_id', '=', record.company_id.id),
                    ('invoice_ids.payment_state', 'in', ['paid', 'partial', 'in_payment']),
                ])
                record.paid_sale_order_ids = paid_so


    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sale_order_id'):
                so_id = self.env['tw.sale.order'].browse(vals['sale_order_id'])
                vals['transaction_name'] = so_id.name
                name = "X" + so_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = name
                vals['date'] = self._get_default_date()
                vals['division'] = so_id.division
        return super(TwSaleOrderCancel, self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a state other than draft!')
        return super(TwSaleOrderCancel, self).unlink()

    # 13: action methods
    def action_confirm(self):
        """
        Confirm the cancellation:
        1. Validate journal configuration
        2. Run validity checks (invoices, shipments)
        3. Cancel pending pickings
        4. Create reversal journal entry
        5. Cancel the sale order
        """
        if self.sale_order_id:
            branch_config_obj = self.company_id.branch_setting_id
            account_setting = branch_config_obj.account_setting_id
            journal_sale_order_cancel_id = account_setting.journal_sale_order_cancel_id
            if not journal_sale_order_cancel_id:
                raise Warning("Attention! The Sale Order Cancel Journal hasn't been configured. Please set it up first in Account Settings.")

            # Check if SO has payments and config disallows cancellation
            if not branch_config_obj.allow_cancel_so_with_payment:
                paid_invoices = self.check_invoices()
                if paid_invoices:
                    raise Warning(
                        f"Sale Order tidak dapat dibatalkan karena sudah memiliki payment pada invoice: {paid_invoices}.\n"
                    )

            self.validity_check()
            self.picking_cancel()
            move = self.create_move(journal_id=journal_sale_order_cancel_id.id)
            if move:
                self.move_id = move.id
            self.sale_order_id._action_cancel()

        return self.cancellation_id.action_confirm()

    def action_view_sale_order(self):
        """Open the linked Sale Order record."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'tw.sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
        }

    def action_request_approval(self):
        self.validity_check()
        return super().action_request_approval(value=5)

    def _get_related_account_moves(self):
        self.ensure_one()
        invoice_moves = self.sale_order_id.invoice_ids.filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )
        additional_moves = self.sale_order_id._get_additional_cancel_account_moves().filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )
        return invoice_moves | additional_moves

    def _get_blocking_account_moves(self):
        self.ensure_one()
        return self.sale_order_id._get_additional_cancel_blocking_moves().filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )

    # 14: private methods
    def check_invoices(self):
        """
        Check if any invoice related to this SO has been paid or reconciled.
        Returns a string with invoice numbers that are blocking cancellation.
        """
        invoice_ids = self._get_related_account_moves()
        message = ""
        checked_invoices = set()
        
        for invoice_id in invoice_ids:
            if invoice_id.name in checked_invoices:
                continue
                
            # Check payment_state - if already paid (partial/paid/in_payment), cannot cancel
            if invoice_id.payment_state in ('paid', 'partial', 'in_payment'):
                message += invoice_id.name + ", "
                checked_invoices.add(invoice_id.name)
                continue

            # Alternative: check if there are reconciled lines
            for line_id in invoice_id.line_ids:
                if line_id.reconciled or line_id.full_reconcile_id:
                    message += invoice_id.name + ", "
                    checked_invoices.add(invoice_id.name)
                    break
        return message.rstrip(", ")

    def check_shipments(self):
        """
        Check whether stock moved by this SO has been returned to its
        originating internal locations.

        This handles multi-step picking as well:
        - Internal -> Internal decreases the source location balance and
          increases the destination location balance.
        - Internal -> External decreases the source internal location balance.
        - External -> Internal increases the destination internal location balance.

        If any internal location still has a negative balance for a product,
        that means the stock has left that location and has not been fully
        returned yet, so SO cancellation must be blocked.
        """
        picking_ids = self.sale_order_id.picking_ids
        qty_by_product_location = {}

        for picking_id in picking_ids:
            if picking_id.state == 'done':
                for move in picking_id.move_ids:
                    product = move.product_id
                    move_qty = move.product_uom_qty

                    if move.location_id.usage == 'internal':
                        key = (product, move.location_id)
                        qty_by_product_location[key] = qty_by_product_location.get(key, 0.0) - move_qty

                    if move.location_dest_id.usage == 'internal':
                        key = (product, move.location_dest_id)
                        qty_by_product_location[key] = qty_by_product_location.get(key, 0.0) + move_qty

        products = set()
        for (product, _location), value in qty_by_product_location.items():
            if float_compare(value, 0.0, precision_rounding=product.uom_id.rounding) < 0:
                products.add(product.name)

        return ", ".join(sorted(products))

    def check_stock_unit(self):
        """
        For Unit division: check if lots are still available in internal location.
        """
        picking_ids = self.sale_order_id.picking_ids
        message = ""
        for picking_id in picking_ids:
            if picking_id.state == 'done':
                for moves in picking_id.move_ids:
                    for line in moves.move_line_ids:
                        if line.lot_id and line.lot_id.location_id.usage != 'internal':
                            message += line.lot_id.name + ", "
        return message.rstrip(", ")

    def validity_check(self):
        """
        Run all validations before confirming cancellation.
        """
        warnings = []
        blocking_moves = self._get_blocking_account_moves()
        
        # Check invoices
        invoice_number = self.check_invoices()
        if invoice_number:
            warnings.append(f"Invoice {invoice_number} sudah dibayar, silahkan lakukan pembatalan Customer Payment terlebih dahulu!")
        if blocking_moves:
            warnings.append(f"Invoice {', '.join(blocking_moves.mapped('name'))} masih terkait dengan transaksi ini, silahkan lakukan pembatalan manual terlebih dahulu!")

        # Check shipments
        shipment_products = self.check_shipments()
        if shipment_products:
            warnings.append(f"Product {shipment_products} belum dikembalikan seluruhnya, silahkan lakukan reverse transfer terlebih dahulu!")

        # For Unit division: additional stock check
        if self.division == 'Unit':
            stock_unit = self.check_stock_unit()
            if stock_unit:
                warnings.append(f"Unit {stock_unit} belum dikembalikan ke internal location!")

        if warnings:
            raise Warning("\n".join(warnings))

    def picking_cancel(self):
        """
        Cancel all pickings that are not yet done.
        """
        picking_ids = self.sale_order_id.picking_ids.filtered(lambda picking: picking.state not in ('done', 'cancel'))
        for picking_id in picking_ids:
            picking_id.action_cancel()

    def create_move(self, journal_id):
        """
        Create reversal journal entry for the cancelled invoices and reconcile them.
        """
        move_line_vals = self._prepare_move_line_default_vals()
        if not move_line_vals:
            return False
            
        move_vals = {
            'name': self.name,
            'journal_id': journal_id,
            'company_id': self.sale_order_id.company_id.id,
            'division': self.sale_order_id.division,
            'period_id': self.period_id.id if self.period_id else False,
            'date': self._get_default_date(),
            'ref': self.sale_order_id.name,
            'line_ids': [Command.create(line_vals) for line_vals in move_line_vals],
        }
        move_created = self.env['account.move'].with_context(skip_date_sequence_check=True).create([move_vals])
        if move_created:
            move_created.action_post()
            
            # Reconcile the reversal lines with original invoice lines
            reversal_lines = move_created.line_ids.filtered(lambda l: l.account_id.reconcile and not l.reconciled)
            for invoice in self._get_related_account_moves():
                invoice_reconcile_lines = invoice.line_ids.filtered(lambda l: l.account_id.reconcile and not l.reconciled)
                for inv_line in invoice_reconcile_lines:
                    # Match reversal line with original line
                    # We match by account, partner, and inverted balance
                    match = reversal_lines.filtered(lambda l: 
                        l.account_id == inv_line.account_id and 
                        l.partner_id == inv_line.partner_id and 
                        abs(l.balance + inv_line.balance) < 0.01
                    )
                    if match:
                        match_line = match[0]
                        try:
                            (inv_line + match_line).reconcile()
                        except Exception:
                            # If reconciliation fails for some reason, we skip it to not block the whole process
                            # though it's unlikely to fail if balance is 0
                            pass
                        reversal_lines -= match_line
                        
        return move_created

    def _prepare_move_line_default_vals(self):
        """
        Prepare reversal move lines from original invoices.
        Swap debit/credit to create reversal effect.
        """
        move_line = []
        invoice_ids = self._get_related_account_moves()
        
        for invoice in invoice_ids:
            for line in invoice.line_ids:
                # Skip zero lines
                if line.debit == 0 and line.credit == 0:
                    continue
                    
                # Calculate amount_currency for reversal
                if line.amount_currency:
                    amount_currency = -line.amount_currency
                else:
                    amount_currency = 0
                    
                move_line.append({
                    'account_id': line.account_id.id,
                    'debit': line.credit,
                    'credit': line.debit,
                    'amount_currency': amount_currency,
                    'currency_id': line.currency_id.id,
                    'name': self.name,
                    'ref': line.ref or self.sale_order_id.name,
                    'company_id': self.sale_order_id.company_id.id,
                    'partner_id': line.partner_id.id if line.partner_id else False,
                    'tax_base_amount': line.tax_base_amount,
                })
        
        return move_line

    def _check_duplicate_transaction(self, name):
        return self.cancellation_id._check_duplicate_transaction(name)
