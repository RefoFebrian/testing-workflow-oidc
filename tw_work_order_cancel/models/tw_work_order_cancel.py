from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from odoo.fields import Command

class TwWorkOrderCancel(models.Model):
    _name = "tw.work.order.cancel"
    _description = 'Work Order Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _order = 'id desc'  

    @api.model
    def _get_default_date(self):
        return datetime.now()

    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Sparepart')

    work_order_id = fields.Many2one('tw.work.order', 'Work Order')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    _sql_constraints = [
        ('unique_work_order_id', 'unique(work_order_id)', 'Work Order pernah diinput sebelumnya !')
    ]
    
    @api.onchange('work_order_id')
    def _onchange_work_order_id(self):
        if self.work_order_id:
            self.transaction_name = self.work_order_id.name
        else:
            self.transaction_name = False

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('work_order_id'):
                wo_id = self.env['tw.work.order'].browse(vals['work_order_id'])
                vals['transaction_name'] = wo_id.name
                name = "X" + wo_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + wo_id.name
                vals['date'] = self._get_default_date()
        return super(TwWorkOrderCancel, self).create(vals_list)

    def action_confirm(self):
        if self.state != 'approved':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')
        if self.work_order_id:
            branch_config_obj = self.company_id.branch_setting_id
            journal_work_order_cancel_id = branch_config_obj.account_setting_id.journal_work_order_cancel_id.id
            if not journal_work_order_cancel_id:
                raise Warning("Attention! The Work Order Cancel Journal hasn't been Created. Please Set it up First.")
            
            self.validity_check()
            self.picking_cancel()
            self.cancellation_id._return_picking(self.work_order_id)
            self.invoice_cancel()
            self.work_order_id._action_cancel()
        
        return self.cancellation_id.action_confirm()
    
    def action_request_approval(self):
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.cancellation_id._get_state_value()}')
        return super().action_request_approval(value=5)

    def action_print_work_order_cancel(self):
        self.ensure_one()
        return self.env.ref('tw_work_order_cancel.action_tw_work_order_cancel_print').report_action(self)

    def _get_related_account_moves(self):
        self.ensure_one()
        invoice_moves = self.work_order_id.invoice_ids.filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )
        additional_moves = self.work_order_id._get_additional_cancel_account_moves().filtered(
            lambda move: move.state == 'posted' and not move.reversed_entry_id
        )
        return invoice_moves | additional_moves

    def _get_external_account_moves_to_block(self):
        self.ensure_one()
        return self.work_order_id._get_additional_cancel_blocking_moves().filtered(
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
            for line_id in invoice_id.line_ids:
                if line_id.reconciled or line_id.full_reconcile_id:
                    message += invoice_id.name + ", "
                    checked_invoices.add(invoice_id.name)
                    break
        return message.rstrip(", ")

    def check_stock_sparepart(self):
        picking_ids = self.work_order_id.picking_ids
        message = ""
        for picking_id in picking_ids:
            if picking_id.state == 'done':
                for moves in picking_id.move_ids:
                    for line in moves.move_line_ids:
                        if line.quant_id.reservation_ids or (line.lot_id and line.lot_id.location_id.usage != 'internal'):                            
                            message += line.lot_id.name if line.lot_id.name else line.display_name + ", "
        return message
    
    def validity_check(self):
        warnings = []
        invoice_number = self.check_invoices()
        external_moves = self._get_external_account_moves_to_block()
        stock_sparepart = False
        if self.division == 'Sparepart':
            stock_sparepart = self.check_stock_sparepart()
        
        if invoice_number:
            warnings.append(
                "Invoice %s sudah dibayar / proses reconcile, silahkan lakukan pembatalan Customer Payment terlebih dahulu!"
                % invoice_number
            )
        if external_moves:
            warnings.append(
                "Journal/Invoice %s masih terkait dengan transaksi Work Order ini. "
                "Silahkan lakukan pembatalan manual terlebih dahulu sebelum Work Order dicancel!"
                % ", ".join(external_moves.mapped('name'))
            )
        if stock_sparepart:
            warnings.append(
                "Sparepart %s belum dikembalikan seluruhnya, silahkan lakukan reverse transfer terlebih dahulu!"
                % stock_sparepart
            )
        if warnings:
            raise Warning("\n".join(warnings))

    def picking_cancel(self):
        picking_ids = self.work_order_id.picking_ids.filtered(lambda picking: picking.state not in ['done', 'cancel'])
        # TODO: cek is_removable pada move line
        for picking_id in picking_ids:
            picking_id.action_cancel()

    def invoice_cancel(self):
        invoice_ids = self._get_related_account_moves()
        branch_config_obj = self.company_id.branch_setting_id
        reversed_move = self.env['account.move']
        for invoice in invoice_ids:
            journal_work_order_cancel_id = branch_config_obj.account_setting_id.journal_work_order_cancel_id.id
            if not journal_work_order_cancel_id:
                raise Warning("Attention! The Work Order Cancel Journal hasn't been Created. Please Set it up First.")
            move_reversal = self.env['account.move.reversal'].sudo().with_context(active_model='account.move', active_ids=invoice.ids).create({
                'date': datetime.now(),
                'journal_id': journal_work_order_cancel_id,
            })
            reversal = move_reversal.sudo().reverse_moves()
            if reversal:
                reversal_move = self.env['account.move'].sudo().browse(reversal.get('res_id', False))
                reversed_move |= reversal_move
                # Re-Write line division
                for line in reversal_move.line_ids:
                    line.write({'division': line.product_id.division})

        if reversed_move:
            reversed_move.filtered(lambda move: move.state == 'draft').sudo().action_post()
            self.move_id = reversed_move[-1].id

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)
