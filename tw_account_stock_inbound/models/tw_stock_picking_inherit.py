# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.tools import float_round

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class twAccountStockPicking(models.Model):
    _inherit = "stock.picking"
    _description = "Stock Picking"

    # 7: defaults methods

    # 8: fields
    volume = fields.Float(string="Volume", default=0.0)
    pricelist_type_value = fields.Char(
        string="Pricelist Type Value",
        related='pricelist_type_id.value'
    )

    # 9: relation fields
    pricelist_type_id = fields.Many2one(
        comodel_name='tw.selection',
        string='Pricelist Type',
        domain=[('type', '=', 'PricelistCategory')],
        help="Pricelist that can be used for supplier cost."
    )

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
    def action_create_invoice_expedition(self):
        """Create the invoice associated to the Expedition."""
        self.ensure_one()

        # Create the journal entry (type 'entry' instead of 'in_invoice')
        invoice_vals = self._prepare_invoice()
        invoice = self.env['account.move'].with_context(
            default_move_type='entry',
            skip_is_manually_modified=True
        ).sudo().with_company(self.company_id.id).create(invoice_vals)

        invoice.suspend_security().with_company(self.company_id).action_post()

        # Link invoice to stock inbound via Many2many
        write_vals = {'move_ids': [(4, invoice.id)]}

        # Only write pricelist_type_id and volume if not already set
        # (first transaction only, since there can be multiple accrue entries)
        stock_inbound = self.stock_inbound_id
        if not stock_inbound.pricelist_type_id:
            write_vals['pricelist_type_id'] = self.pricelist_type_id.id
        if not stock_inbound.volume:
            write_vals['volume'] = self.volume

        stock_inbound.suspend_security().write(write_vals)
        return invoice

    # 14: private methods
    def _process_validate_picking(self):
        """Process picking validation and create expedition journal entry.

        Logic per price type:
        - Product/Category: Create entry per picking (multiple entries allowed)
        - Volume/Delivery: Create entry only once (skip if already exists)
        """
        res = super(twAccountStockPicking, self)._process_validate_picking()

        if not self.stock_inbound_id:
            return res

        pricelist_type = self.pricelist_type_value
        stock_inbound = self.stock_inbound_id

        # Volume/Delivery: Skip if entry already exists
        if pricelist_type in ('volume', 'delivery'):
            if stock_inbound.move_ids:
                # Entry already created, skip
                return res

        # Create invoice and stock valuation layers
        invoice = self.action_create_invoice_expedition()
        self._create_stock_valuation_layers(invoice)

        return res

    def _get_expedition_pricelist(self):
        """Get the pricelist from the expedition based on the picking's division.

        Returns the correct pricelist depending on division:
        - 'Unit'      -> expedition partner's pricelist_expedition_unit_id
        - 'Sparepart' -> expedition partner's pricelist_expedition_sparepart_id

        Returns:
            recordset: The pricelist record

        Raises:
            Warning: If no expedition or the matching pricelist field is not set
        """
        exspedition_obj = self.stock_inbound_id.expedition_id
        division = self.division

        if division == 'Unit':
            pricelist = exspedition_obj.with_company(self.company_id).pricelist_expedition_unit_id
            label = 'Pricelist Unit'
        elif division == 'Sparepart':
            pricelist = exspedition_obj.with_company(self.company_id).pricelist_expedition_sparepart_id
            label = 'Pricelist Sparepart'

        if not pricelist:
            raise Warning(
                f"Expedition {label} is not set for {exspedition_obj.name}.\n"
                f"- Go to the Expedition Master.\n"
                f"- Set the '{label}' field to proceed.\n"
                "This configuration is required for proper operation."
            )
        return pricelist


    def _get_expedition_price(self, pricelist_obj, product):
        """Get expedition price from pricelist for a product.

        Validates that an applicable pricelist rule exists before returning
        the price. If no rule is found, raises an error to prevent journal
        entries with incorrect fallback prices (e.g. product list_price).

        Args:
            pricelist_obj: The pricelist recordset
            product: The product recordset to get price for

        Returns:
            float: The price from pricelist

        Raises:
            Warning: If no applicable pricelist rule is found for the product
        """
        pricelist = pricelist_obj.with_company(self.company_id)
        # Use _compute_price_rule to get both price and rule_id
        # kwargs category_price is passed through to _get_applicable_rules
        price_rule = pricelist._compute_price_rule(
            product, 1, category_price=self.pricelist_type_id.id
        )
        price, rule_id = price_rule.get(product.id, (0, False))

        if not rule_id:
            raise Warning(
                f"No expedition pricelist rule found for product '{product.display_name}'.\n"
                f"- Pricelist: '{pricelist_obj.name}'\n"
                f"- Pricelist Type: '{self.pricelist_type_id.name}'\n"
                "Please configure the correct pricelist item for this product."
            )
        return price

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice."""
        self.ensure_one()

        branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
        if not branch_setting_obj.account_setting_id:
            raise Warning(
                "Account setting is not set for this branch.\n"
                "- Go to the Master Branch Setting.\n"
                "- Set the 'Account Setting' to proceed.\n"
                "This configuration is required to create accounting entries."
            )
        if not branch_setting_obj.account_setting_id.journal_expedition_id:
            raise Warning(
                "Journal Expedition is not set for this branch.\n"
                "- Go to the Account Setting.\n"
                "- Set the 'Journal Ekspedisi'.\n"
                "This configuration is required to create Accrue Expedition."
            )

        exspedition_obj = self.stock_inbound_id.expedition_id
        pricelist_obj = self._get_expedition_pricelist()
        journal_obj = branch_setting_obj.account_setting_id.journal_expedition_id

        invoice_vals = {
            'ref': f'{self.name} - {self.origin or ""}',
            'move_type': 'entry',
            'currency_id': self.company_id.currency_id.id,
            'journal_id': journal_obj.id,
            'partner_id': exspedition_obj.id,
            'invoice_origin': self.name,
            'date': fields.Date.today(),
            'line_ids': [],
            'company_id': self.company_id.id,
        }

        # For 'entry' type, we need balanced debit/credit lines in line_ids
        debit_line = self._prepare_debit_line(journal_obj, pricelist_obj)
        credit_line = self._prepare_credit_line(journal_obj, pricelist_obj)
        invoice_vals['line_ids'].append((0, 0, debit_line))
        invoice_vals['line_ids'].append((0, 0, credit_line))
        return invoice_vals

    def _prepare_debit_line(self, journal_obj, pricelist_obj):
        """Prepare debit line for journal entry (stock valuation account).

        All types return a single combined debit line:
        - Product: Sum(qty × price per product template)
        - Category: Sum(qty × price per category)
        - Volume: Fixed amount from pricelist
        - Delivery: Fixed amount from pricelist
        """
        self.ensure_one()
        pricelist_type = self.pricelist_type_value

        # Get stock valuation account from first product's category
        first_move = self.move_ids[:1]
        if not first_move:
            raise Warning('No stock moves found for this picking.')

        stock_valuation_account = first_move.product_id.categ_id.property_stock_valuation_account_id
        if not stock_valuation_account:
            raise Warning(
                f'Stock Valuation Account is not set for category {first_move.product_id.categ_id.name}.'
            )

        # Calculate total amount based on pricelist type
        total_amount = self._calculate_expedition_amount(pricelist_obj, pricelist_type)

        # Calculate total quantity received
        total_qty = sum(move.quantity for move in self.move_ids)

        return {
            'name': f'Accrue Expedition Cost for {self.stock_inbound_id.expedition_id.name} ({self.stock_inbound_id.name} - {self.name})',
            'quantity': total_qty,
            'debit': total_amount,
            'credit': 0.0,
            'account_id': stock_valuation_account.id,
            'partner_id': self.stock_inbound_id.expedition_id.id,
            'company_id': self.company_id.id,
        }

    def _prepare_credit_line(self, journal_obj, pricelist_obj):
        """Prepare credit line for journal entry (expedition payable account)."""
        self.ensure_one()

        # Default to journal's default credit account
        account_obj = journal_obj.default_credit_account_id
        if not account_obj:
            raise Warning(f'Default Credit Account is not set for journal {journal_obj.name}.')

        # Calculate total amount using same method as debit line
        pricelist_type = self.pricelist_type_value
        total_amount = self._calculate_expedition_amount(pricelist_obj, pricelist_type)

        # Calculate total quantity received
        total_qty = sum(move.quantity for move in self.move_ids)

        return {
            'name': f'Accrue Expedition Cost for {self.stock_inbound_id.expedition_id.name} ({self.stock_inbound_id.name} - {self.name})',
            'quantity': total_qty,
            'debit': 0.0,
            'credit': total_amount,
            'account_id': account_obj.id,
            'partner_id': self.stock_inbound_id.expedition_id.id,
            'company_id': self.company_id.id,
        }

    def _calculate_expedition_amount(self, pricelist_obj, pricelist_type):
        """Calculate total expedition amount based on pricelist type.

        Args:
            pricelist_obj: The pricelist recordset
            pricelist_type: One of 'product', 'category', 'volume', 'delivery'

        Returns:
            float: Total amount for expedition cost
        """
        total_amount = 0.0

        if pricelist_type == 'product':
            # Sum(qty × price per product)
            product_qty = {}
            for move in self.move_ids:
                # Skip products with manual valuation (e.g., extras)
                if move.product_id.categ_id.property_valuation == 'manual_periodic' or move.product_id.division in ('Extras','Umum'):
                    continue

                product = move.product_id
                if product not in product_qty:
                    product_qty[product] = 0
                product_qty[product] += move.quantity

            for product, qty in product_qty.items():
                price = self._get_expedition_price(pricelist_obj, product)
                total_amount += qty * price

        elif pricelist_type == 'category':
            # Sum(qty × price per category)
            categ_qty = {}
            for move in self.move_ids:
                # Skip products with manual valuation (e.g., extras)
                if move.product_id.categ_id.property_valuation == 'manual_periodic':
                    continue
                    
                categ = move.product_id.categ_id
                if categ not in categ_qty:
                    categ_qty[categ] = {'qty': 0, 'product': move.product_id}
                categ_qty[categ]['qty'] += move.quantity

            for categ, data in categ_qty.items():
                price = self._get_expedition_price(pricelist_obj, data['product'])
                total_amount += data['qty'] * price

        elif pricelist_type in ('volume', 'delivery'):
            # Fixed amount from pricelist (use first product to get price)
            first_product = self.move_ids[:1].product_id
            if first_product:
                price = self._get_expedition_price(pricelist_obj, first_product)
                total_amount = price

        return total_amount

    def _create_stock_valuation_layers(self, invoice):
        """Create stock valuation layers for each lot in the picking.

        SVL Value per price type:
        - Product/Category: Fixed amount from pricelist (already per unit)
        - Volume/Delivery: Fixed amount ÷ total qty in picking
        """
        self.ensure_one()

        pricelist_type = self.pricelist_type_value
        pricelist_obj = self._get_expedition_pricelist()

        # Calculate total qty for Volume/Delivery distribution
        total_qty = sum(move.quantity for move in self.move_ids_without_package) or 1

        # For Volume/Delivery, get fixed amount to distribute
        fixed_amount = 0
        if pricelist_type in ('volume', 'delivery'):
            first_product = self.move_ids_without_package[:1].product_id
            fixed_amount = self._get_expedition_price(pricelist_obj, first_product)

        # Create stock valuation layers for each move line
        for move in self.move_ids_without_package:
            # Skip products with manual valuation (e.g., extras)
            if move.product_id.categ_id.property_valuation == 'manual_periodic':
                continue
                
            # Determine value per unit based on pricelist type
            if pricelist_type in ('product', 'category'):
                # Fixed amount from pricelist (per unit)
                price = self._get_expedition_price(pricelist_obj, move.product_id)
                unit_value = price
            else:
                # Volume/Delivery: Fixed ÷ total qty
                unit_value = fixed_amount / total_qty

            if move.move_line_ids:
                for move_line in move.move_line_ids:
                    value = float_round(
                        unit_value,
                        precision_rounding=move.company_id.currency_id.rounding
                    )

                    # Find the topmost parent valuation layer for this product and lot
                    domain = [
                        ('product_id', '=', move.product_id.id),
                        ('stock_valuation_layer_id', '=', False),
                    ]
                    if move_line.lot_id:
                        domain.append(('lot_id', '=', move_line.lot_id.id))

                    # Get the oldest valuation layer (FIFO)
                    top_layer = self.env['stock.valuation.layer'].suspend_security().search(
                        domain,
                        order='create_date asc',
                        limit=1
                    )

                    if top_layer:
                        # Update the remaining value of the top layer
                        top_layer.suspend_security().write({
                            'remaining_value': (top_layer.remaining_value or 0) + value
                        })
                        # Create the stock valuation layer
                        svl_vals = {
                            'value': value,
                            'quantity': 0,
                            'product_id': move.product_id.id,
                            'stock_move_id': move.id,
                            'company_id': self.company_id.id,
                            'description': (
                                f'Expedition-{invoice.name} Cost for '
                                f'{move.product_id.display_name} from {self.name}'
                            ),
                            'stock_valuation_layer_id': top_layer.id,
                            'account_move_id': invoice.id,
                        }
                        if move_line.lot_id:
                            svl_vals['lot_id'] = move_line.lot_id.id

                        self.env['stock.valuation.layer'].suspend_security().create(svl_vals)

                        # Update freight_cost pada stock.lot sesuai expedition cost
                        if move_line.lot_id:
                            move_line.lot_id.suspend_security().write({
                                'freight_cost': value,
                            })
