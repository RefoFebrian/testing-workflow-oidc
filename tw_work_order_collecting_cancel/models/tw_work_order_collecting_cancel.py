from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from odoo.fields import Command

class TwWorkOrderCollectingCancel(models.Model):
    _name = "tw.work.order.collecting.cancel"
    _description = 'Work Order Collecting Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _order = 'id desc'  

    @api.model
    def _get_default_date(self):
        return datetime.now()

    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Sparepart')

    work_order_collecting_id = fields.Many2one('tw.work.order.collecting', 'Work Order Collecting')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    _sql_constraints = [
        ('unique_work_order_collecting_id', 'unique(work_order_collecting_id)', 'Work Order Collecting pernah diinput sebelumnya !')
    ]
    
    @api.onchange('work_order_collecting_id')
    def _onchange_work_order_collecting_id(self):
        if self.work_order_collecting_id:
            self.transaction_name = self.work_order_collecting_id.name
        else:
            self.transaction_name = False

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('work_order_collecting_id'):
                wo_id = self.env['tw.work.order.collecting'].browse(vals['work_order_collecting_id'])
                vals['transaction_name'] = wo_id.name
                name = "X" + wo_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + wo_id.name
                vals['date'] = self._get_default_date()
        return super(TwWorkOrderCollectingCancel, self).create(vals_list)

    def action_confirm(self):
        if self.work_order_collecting_id:
            branch_config_obj = self.company_id.branch_setting_id
            journal_wo_collecting_cancel_id = branch_config_obj.account_setting_id.journal_wo_collecting_cancel_id.id
            if not journal_wo_collecting_cancel_id:
                raise Warning("Attention! The Work Order Collecting Cancel Journal hasn't been Created. Please Set it up First.")

            self._check_validity()
            self.invoice_cancel()
            self.move_id.sudo().action_post()
            
            # Cancel Work Order Collecting
            self.work_order_collecting_id._action_cancel()
        
        return self.cancellation_id.action_confirm()
    
    def action_request_approval(self):
        return super().action_request_approval(value=5)

    def action_print_work_order_collecting_cancel(self):
        self.ensure_one()
        return self.env.ref('tw_work_order_collecting_cancel.action_tw_work_order_collecting_cancel_print').report_action(self)

    def check_invoices(self):
        invoice_id = self.work_order_collecting_id.invoice_id
        message = ""
        # Check payment_state - if already paid (partial/paid/in_payment), cannot cancel
        if invoice_id.payment_state in ('paid', 'partial', 'in_payment'):
            message += invoice_id.name + ", "
        return message.rstrip(", ")

    def check_stock_sparepart(self):
        picking_ids = self.work_order_collecting_id.picking_ids
        message = ""
        for picking_id in picking_ids:
            if picking_id.state == 'done':
                for moves in picking_id.move_ids:
                    for line in moves.move_line_ids:
                        if line.quant_id.reservation_id or (line.lot_id and line.lot_id.location_id.usage != 'internal'):                            
                            message += line.lot_id.name if line.lot_id.name else line.display_name + ", "
        return message

    def invoice_cancel(self):
        invoice_id = self.work_order_collecting_id.invoice_id
        branch_config_obj = self.company_id.branch_setting_id
        journal_wo_collecting_cancel_id = branch_config_obj.account_setting_id.journal_wo_collecting_cancel_id.id
        if not journal_wo_collecting_cancel_id:
            raise Warning("Attention! The Work Order Collecting Cancel Journal hasn't been Created. Please Set it up First.")
        move_reversal = self.env['account.move.reversal'].sudo().with_context(active_model='account.move', active_ids=invoice_id.ids).create({
            'date': datetime.now(),
            'journal_id': journal_wo_collecting_cancel_id,
        })
        reversal = move_reversal.sudo().reverse_moves()
        if reversal:
            self.move_id = reversal.get('res_id',False)
            # Re-Write line division
            for line in self.move_id.line_ids:
                line.write({'division': self.work_order_collecting_id.division})

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)


    def _check_validity(self):
        for rec in self:
            rec.check_invoices()
            if not rec.work_order_collecting_id:
                raise Warning(_('Please select a Work Order Collecting to cancel.'))
            if rec.work_order_collecting_id.state != 'posted':
                raise Warning(_('Only Posted Work Order Collecting can be cancelled.'))
        return True