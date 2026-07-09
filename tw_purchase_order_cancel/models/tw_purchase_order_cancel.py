# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwPurchaseOrderCancel(models.Model):
    _name = "tw.purchase.order.cancel"
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = 'Purchase Order Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()

    # 8: fields

    # 9: relation fields
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')
    
    # Computed fields for smart buttons
    picking_count = fields.Integer(compute='_compute_picking_count', string='Picking Count')
    
    @api.depends('purchase_order_id', 'purchase_order_id.picking_ids')
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.purchase_order_id.picking_ids) if rec.purchase_order_id else 0

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.purchase_order_id = False

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order_id(self):
        if self.purchase_order_id:
            self.transaction_name = self.purchase_order_id.name
            # Update name saat ganti PO di draft
            if self.state == 'draft' or not self.state:
                self.name = 'X' + self.purchase_order_id.name
        else:
            self.transaction_name = False
            self.name = False
                

    # 12: override methods
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a state other than draft!')
            else:
                raise Warning('Warning! \nCannot delete records!')

        return super(TwPurchaseOrderCancel, self).unlink()

    # 13: action methods
    def action_view_purchase_order(self):
        """Open Purchase Order form view"""
        self.ensure_one()
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.purchase_order_id.id,
            'context': {'create': False},
        }
    
    def action_view_pickings(self):
        """Open Pickings list view"""
        self.ensure_one()
        picking_ids = self.purchase_order_id.picking_ids
        return {
            'name': 'Pickings',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', picking_ids.ids)],
            'context': {'create': False},
        }

    # 14: private methods

    _sql_constraints = [
        ('unique_purchase_order_id', 'unique(purchase_order_id)', 'Purchase Order pernah diinput sebelumnya !')
    ]
    
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('purchase_order_id'):
                po_id = self.env['purchase.order'].browse(vals['purchase_order_id'])
                vals['transaction_name'] = po_id.name
                name = "X" + po_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + po_id.name
                vals['date'] = self._get_default_date()
        return super(TwPurchaseOrderCancel, self).create(vals_list)
    
    def action_request_approval(self):
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.state}')
        return super().action_request_approval(value=5)

    def _get_related_account_moves(self):
        """Get all posted account moves that must be considered on PO cancellation."""
        self.ensure_one()

        purchase_moves = self.purchase_order_id.sudo().invoice_ids.filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )
        additional_moves = self.purchase_order_id.sudo()._get_additional_cancel_account_moves().filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )

        return purchase_moves | additional_moves

    def _get_blocking_account_moves(self):
        self.ensure_one()
        return self.purchase_order_id.sudo()._get_additional_cancel_blocking_moves().filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )

    def check_invoices(self):
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
            payable_lines = invoice_id.line_ids.filtered(lambda l: l.account_id.account_type == 'liability_payable')
            for line_id in payable_lines:
                if line_id.reconciled or line_id.full_reconcile_id:
                    message += invoice_id.name + ", "
                    checked_invoices.add(invoice_id.name)
                    break
        return message.rstrip(", ")

    def check_stock_unit(self):
        picking_ids = self.purchase_order_id.sudo().picking_ids
        message = ""
        for picking_id in picking_ids:
            if picking_id.state == 'done':
                for moves in picking_id.move_ids:
                    for line in moves.move_line_ids:
                        if line.location_id.usage not in ('supplier','internal','transit'):
                            name = line.lot_id.name if line.lot_id else line.product_id.name
                            message += name + ", "
            if message:
                message = "Picking %s : %s \n" % (picking_id.name, message)
        return message.rstrip(", ")
    
    def check_stock_sparepart(self):
        message = ""
        list_prod = []
        picking_ids = self.purchase_order_id.sudo().picking_ids
        for picking_id in picking_ids:
            if picking_id.state == 'done':
                for move in picking_id.move_ids:
                    list_prod.append(move.product_id)

        for lines in self.purchase_order_id.sudo().order_line:
            if lines.product_id.id not in list_prod:
                continue
            quant_ids = self.env['stock.quant'].search([
                ('location_id.company_id', '=', self.company_id.id),
                ('product_id', '=', lines.product_id.id),
                ('reservation_ids', '=', False),
                ('location_id.usage', '=', 'internal')])
            qty_avb = sum(quant.qty for quant in quant_ids)
            if qty_avb < lines.product_qty:
                message += lines.product_id.name + ", "
        return message
    
    def validity_check(self):
        invoice_warning = ""
        invoice_name = self.check_invoices()
        external_moves = self._get_blocking_account_moves()
        stock_unit = False
        stock_sparepart = False
        if self.division == 'Unit':
            stock_unit = self.check_stock_unit()
        elif self.division == 'Sparepart':
            stock_sparepart = self.check_stock_sparepart()
        
        if invoice_name:
            invoice_warning = "Invoice " + invoice_name + " sudah dibayar / Proses, silahkan lakukan pembatalan Customer/Supplier Payment terlebih dahulu!"
        if external_moves:
            invoice_warning = "Invoice " + ", ".join(external_moves.mapped('name')) + " masih terkait dengan transaksi ini, silahkan lakukan pembatalan manual terlebih dahulu!"
        if stock_unit:
            invoice_warning = "Barang belum di return / sudah dijual / direserved di sales order untuk \n " + stock_unit + "\nSilahkan lakukan Return / pembatalan Sales Order terlebih dahulu!"
        if stock_sparepart:
            invoice_warning = "Quantity sparepart " + stock_sparepart + " yang dibatalkan melebihi stock di cabang, silahkan lakukan pembatalan Work Order/Mutasi terlebih dahulu!"
        if invoice_warning:
            raise Warning(invoice_warning)
    
    def picking_cancel(self):
        picking_ids = self.purchase_order_id.sudo().picking_ids.filtered(lambda picking: picking.state != 'done')
        # TODO: cek is_removable pada move line
        for picking_id in picking_ids:
            picking_id.action_cancel()

    def _get_atpm_code(self):
        """Get ATPM code (e.g., 'AHM') for Main Dealer."""
        return self.env['res.company'].get_default_main_dealer_atpm_code()

    def _rename_lots_on_cancel(self):
        """
        Rename lot/serial number dengan prefix 'X' untuk barang yang sudah diterima.
        Berlaku untuk Unit dan Sparepart.
        Skip serial number length validation dengan context flag.
        """
        for picking in self.purchase_order_id.sudo().picking_ids.filtered(lambda p: p.state == 'done'):
            for move in picking.move_ids:
                for line in move.move_line_ids:
                    if line.lot_id:
                        # Skip serial number length check saat rename dari PO Cancel
                        line.lot_id.with_context(skip_serial_length_check=True).write({
                            'name': 'X' + line.lot_id.name
                        })
                    
    def _return_picking(self):
        self.cancellation_id.sudo()._return_picking(self.purchase_order_id.sudo())
    
    def invoice_cancel(self):
        invoice_ids = self._get_related_account_moves()
        branch_config_obj = self.company_id.branch_setting_id
        reversed_move = self.env['account.move']
        for invoice in invoice_ids:
            journal_purchase_unit_id = branch_config_obj.account_setting_id.journal_purchase_unit_id.id
            journal_purchase_sparepart_id = branch_config_obj.account_setting_id.journal_purchase_sparepart_id.id
            journal_purchase_umum_id = branch_config_obj.account_setting_id.journal_purchase_umum_id.id

            journal_purchase_cancel_id = branch_config_obj.account_setting_id.journal_purchase_order_cancel_id.id
            if invoice.journal_id not in (journal_purchase_unit_id,journal_purchase_sparepart_id,journal_purchase_umum_id):
                journal_purchase_cancel_id = invoice.journal_id.id
            if not journal_purchase_cancel_id:
                raise Warning("Attention! The Purchase Order Cancel Journal hasn't been Created. Please Set it up First.")
            move_reversal = self.env['account.move.reversal'].sudo().with_context(active_model='account.move', active_ids=invoice.ids).create({
                'date': datetime.now(),
                'journal_id': journal_purchase_cancel_id,
            })
            reversal = move_reversal.sudo().reverse_moves()
            if reversal:
                reversed_move |= self.env['account.move'].sudo().browse(reversal.get('res_id', False))

        if reversed_move:
            reversed_move.filtered(lambda move: move.state == 'draft').sudo().action_post()
            self.move_id = reversed_move[-1].id
        
    def action_confirm(self):
        # Skip mail notification dan bypass multi-company rules
        self = self.with_context(
            mail_create_nosubscribe=True,
            mail_notrack=True,
            tracking_disable=True,
            mail_auto_delete=False,
            no_reset_password=True,
        )
        
        if self.purchase_order_id:    
            # Use suspend_security untuk bypass multi-company record rules
            po = self.purchase_order_id.sudo()
            
            self.validity_check()
            self.picking_cancel()
            self._rename_lots_on_cancel()  # Rename lot dengan prefix X
            self._return_picking()
            self.invoice_cancel()
            
            # Cancel PO dengan suspend_security
            self.purchase_order_id.sudo().button_cancel()
        return self.cancellation_id.action_confirm()
        

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)
