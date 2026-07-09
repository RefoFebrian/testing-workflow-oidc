# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools.float_utils import float_compare

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwDealerSaleOrderCancel(models.Model):
    _name = "tw.dealer.sale.order.cancel"
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = 'Dealer Sale Order Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'  

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()
    
    
    # 8: fields

    # 9: relation fields
    dealer_sale_order_id = fields.Many2one('tw.dealer.sale.order', 'Dealer Sale Order')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    # 10: constraints & sql constraints

    _sql_constraints = [
        ('unique_dealer_sale_order_id', 'unique(dealer_sale_order_id)', 'Dealer Sale Order pernah diinput sebelumnya !')
    ]
    
    # 11: compute/depends & on change methods
    @api.onchange('dealer_sale_order_id')
    def _onchange_dealer_sale_order_id(self):
        if self.dealer_sale_order_id:
            self.transaction_name = self.dealer_sale_order_id.name
        else:
            self.transaction_name = False
                

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('dealer_sale_order_id'):
                dso_id = self.env['tw.dealer.sale.order'].browse(vals['dealer_sale_order_id'])
                vals['transaction_name'] = dso_id.name
                name = "X" + dso_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + dso_id.name
                vals['date'] = self._get_default_date()
        return super(TwDealerSaleOrderCancel, self).create(vals_list)
    
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise UserError('Warning! \nTidak dapat menghapus data dengan state selain draft!')
            else:
                raise UserError('Warning! \nTidak dapat menghapus data!')

        return super(TwDealerSaleOrderCancel, self).unlink()

    # 13: action methods
    def action_confirm(self):
        if self.state != 'approved':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')

        if self.dealer_sale_order_id:
            branch_config_obj = self.company_id.branch_setting_id
            journal_dealer_sale_order_cancel_id = branch_config_obj.account_setting_id.journal_dealer_sale_order_cancel_id.id
            if not journal_dealer_sale_order_cancel_id:
                raise UserError("Perhatian! Journal Pembatalan DSO belum dibuat. Silakan buat terlebih dahulu.")

            self.validity_check()
            self.picking_cancel()

            # Automatically unreconcile related moves (invoices & AL/additional moves) and HL entries
            related_moves = self._get_related_account_moves()
            hl_lines = self.dealer_sale_order_id.payment_ids.mapped('payment_entry_id')
            lines_to_unreconcile = (related_moves.line_ids | hl_lines).filtered(
                lambda l: l.matched_credit_ids or l.matched_debit_ids or l.full_reconcile_id
            )
            if lines_to_unreconcile:
                lines_to_unreconcile.sudo().remove_move_reconcile()

            move = self.create_move(journal_id=journal_dealer_sale_order_cancel_id)
            if move:
                self.move_id = move.id
            self.cancel_faktur_pajak()
            for line in self.dealer_sale_order_id.order_line:
                if line.lot_id:
                    line.lot_id.write({
                        'sales_order_reserved_id': False,
                        'customer_reserved_id': False,
                        'payment_type_id': False,
                        'dealer_sale_order_id': False,
                        'finco_id': False,
                        'partner_id': False,
                        'customer_stnk_id': False,
                        'biro_jasa_id': False,
                        'do_date': False,
                        'invoice_date': False,
                        'downpayment': False,
                        'tenor': False,
                        'installment': False,
                        'accure_bbn_move_id': False,
                        'accrue_bbn_move_line_ids': False,
                    })
            self.dealer_sale_order_id.write({'state': 'cancel'})

        return self.cancellation_id.action_confirm()

    def action_view_dealer_sale_order(self):
        """Open the linked Dealer Sale Order record."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dealer Sale Order',
            'res_model': 'tw.dealer.sale.order',
            'view_mode': 'form',
            'res_id': self.dealer_sale_order_id.id,
        }

    def action_request_approval(self):
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')
        return super().action_request_approval(value=5)

    def _get_related_account_moves(self):
        self.ensure_one()
        invoice_moves = self.dealer_sale_order_id.invoice_ids.filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )
        additional_moves = self.dealer_sale_order_id._get_additional_cancel_account_moves().filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )
        moves = invoice_moves | additional_moves
        
        # Dynamically find AL moves (allocation journal entries) reconciled with these moves
        account_conf = self.dealer_sale_order_id.company_id.branch_setting_id.account_setting_id
        allocation_journal = account_conf.journal_dso_downpayment_allocation_id if account_conf else False
        if allocation_journal:
            reconciled_moves = self.env['account.move']
            for move in moves:
                for line in move.line_ids:
                    if line.reconciled or line.matched_credit_ids or line.matched_debit_ids:
                        reconciled_lines = self.env['account.move.line']
                        if line.full_reconcile_id:
                            reconciled_lines |= line.full_reconcile_id.reconciled_line_ids
                        for partial in (line.matched_credit_ids | line.matched_debit_ids):
                            reconciled_lines |= partial.credit_move_id | partial.debit_move_id
                        for r_line in reconciled_lines:
                            if r_line.move_id.journal_id == allocation_journal and r_line.move_id.state == 'posted' and not r_line.move_id.reversed_entry_id:
                                reconciled_moves |= r_line.move_id
            moves |= reconciled_moves
            
        return moves

    def _get_blocking_account_moves(self):
        self.ensure_one()
        return self.dealer_sale_order_id._get_additional_cancel_blocking_moves().filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )

    # 14: private methods
    def check_invoices(self):
        invoice_ids = self._get_related_account_moves()
        message = ""
        checked_invoices = set()
        
        # Get allocation journal
        account_conf = self.dealer_sale_order_id.company_id.branch_setting_id.account_setting_id
        allocation_journal = account_conf.journal_dso_downpayment_allocation_id if account_conf else False

        # Build allowed line IDs (invoices, AL moves/additional moves, and HL lines/moves)
        allowed_line_ids = set()
        allowed_line_ids.update(self.dealer_sale_order_id.invoice_ids.line_ids.ids)
        
        additional_moves = self.dealer_sale_order_id._get_additional_cancel_account_moves()
        allowed_line_ids.update(additional_moves.line_ids.ids)
        
        hl_lines = self.dealer_sale_order_id.payment_ids.mapped('payment_entry_id')
        if hl_lines:
            allowed_line_ids.update(hl_lines.ids)
            allowed_line_ids.update(hl_lines.move_id.line_ids.ids)
            
        # Dynamically discover and allow AL moves/HL moves reconciled with invoice lines
        for invoice_id in invoice_ids:
            for line_id in invoice_id.line_ids:
                if line_id.reconciled or line_id.matched_credit_ids or line_id.matched_debit_ids:
                    reconciled_lines = self.env['account.move.line']
                    if line_id.full_reconcile_id:
                        reconciled_lines |= line_id.full_reconcile_id.reconciled_line_ids
                    for partial in (line_id.matched_credit_ids | line_id.matched_debit_ids):
                        reconciled_lines |= partial.credit_move_id | partial.debit_move_id
                    for r_line in reconciled_lines:
                        if (allocation_journal and r_line.move_id.journal_id == allocation_journal) or (hl_lines and r_line.id in hl_lines.ids) or (hl_lines and r_line.move_id in hl_lines.move_id):
                            allowed_line_ids.update(r_line.move_id.line_ids.ids)
            
        for invoice_id in invoice_ids:
            if invoice_id.name in checked_invoices:
                continue

            for line_id in invoice_id.line_ids:
                if line_id.reconciled or line_id.matched_credit_ids or line_id.matched_debit_ids:
                    # Find all lines reconciled with this line
                    reconciled_lines = self.env['account.move.line']
                    if line_id.full_reconcile_id:
                        reconciled_lines |= line_id.full_reconcile_id.reconciled_line_ids
                    for partial in (line_id.matched_credit_ids | line_id.matched_debit_ids):
                        reconciled_lines |= partial.credit_move_id | partial.debit_move_id
                        
                    # Check if any reconciled line is not allowed
                    unallowed_lines = [l for l in reconciled_lines if l.id not in allowed_line_ids]
                    if unallowed_lines:
                        message += invoice_id.name + ", "
                        checked_invoices.add(invoice_id.name)
                        break
        return message.rstrip(", ")

    def check_shipments(self):
        """Cek apakah stock dari DSO sudah kembali ke lokasi internal asal.

        Berlaku juga untuk multi-step picking:
        - Internal -> Internal: kurangi saldo lokasi asal, tambah lokasi tujuan.
        - Internal -> External: kurangi saldo lokasi asal.
        - External -> Internal: tambah saldo lokasi tujuan.

        Jika masih ada saldo negatif pada lokasi internal, berarti stock belum
        kembali seluruhnya dan DSO tidak boleh dicancel.
        """
        picking_ids = self.dealer_sale_order_id.picking_ids
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

    def check_permohonan_faktur(self):
        """Cek apakah lot pada DSO line sudah memiliki tanggal permohonan faktur.
        Field vehicle_document_request_date berasal dari module tw_vehicle_document,
        pengecekan dilakukan secara dinamis tanpa dependency ke module tersebut.
        """
        if 'vehicle_document_request_date' not in self.env['stock.lot']._fields:
            return

        for dso_line in self.dealer_sale_order_id.order_line:
            if dso_line.lot_id and dso_line.lot_id.vehicle_document_request_date:
                raise UserError("Silahkan lakukan pembatalan Permohonan Faktur terlebih dahulu!")

    def cancel_faktur_pajak(self):
        """Cancel faktur pajak yang terkait dengan DSO.
        Field faktur_pajak_id berasal dari module tw_dealer_sale_order_faktur_pajak,
        pengecekan dilakukan secara dinamis tanpa dependency ke module tersebut.
        """
        if 'faktur_pajak_id' not in self.env['tw.dealer.sale.order']._fields:
            return

        if self.dealer_sale_order_id.faktur_pajak_id:
            self.dealer_sale_order_id.faktur_pajak_id.write({'state': 'cancel'})

    def validity_check(self):
        invoice_number = self.check_invoices()
        shipment_products = self.check_shipments()
        blocking_moves = self._get_blocking_account_moves()

        warnings = []
        self.check_permohonan_faktur()
        if invoice_number:
            warnings.append(f"Invoice {invoice_number} sudah dibayar, silahkan lakukan pembatalan Customer Payment terlebih dahulu!")
        if blocking_moves:
            warnings.append(f"Invoice {', '.join(blocking_moves.mapped('name'))} masih terkait dengan transaksi ini, silahkan lakukan pembatalan manual terlebih dahulu!")
        if shipment_products:
            warnings.append(f"Product {shipment_products} belum dikembalikan seluruhnya, silahkan lakukan reverse transfer terlebih dahulu!")
        if warnings:
            raise UserError("\n".join(warnings))

    def picking_cancel(self):
        picking_ids = self.dealer_sale_order_id.picking_ids.filtered(lambda picking: picking.state not in ('done', 'cancel'))
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
            'company_id': self.dealer_sale_order_id.company_id.id,
            'division': self.dealer_sale_order_id.division,
            'period_id': self.period_id.id if self.period_id else False,
            'date': self._get_default_date(),
            'ref': self.dealer_sale_order_id.name,
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
                            pass
                        reversal_lines -= match_line

        return move_created
    
    def _prepare_move_line_default_vals(self):
        """Prepare reversal move lines from original invoices.
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
                    'ref': line.ref or self.dealer_sale_order_id.name,
                    'company_id': self.dealer_sale_order_id.company_id.id,
                    'partner_id': line.partner_id.id if line.partner_id else False,
                    'tax_base_amount': line.tax_base_amount,
                })

        return move_line

    def _check_duplicate_transaction(self, name):
        return self.cancellation_id._check_duplicate_transaction(name)
