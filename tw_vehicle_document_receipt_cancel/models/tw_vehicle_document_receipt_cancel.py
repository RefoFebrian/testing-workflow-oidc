# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class TwVehicleDocumentReceiptCancel(models.Model):
    _name = "tw.vehicle.document.receipt.cancel"
    _description = 'Penerimaan STNK Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _order = 'id desc'

    # Fields
    name = fields.Char(string="Name", compute='_compute_name', store=True, default='New', copy=False)
    
    # Relations
    vehicle_document_receipt_id = fields.Many2one(
        'tw.vehicle.registration.receipt',
        string='Document Receipt',
    )
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')
    cancel_line_ids = fields.One2many('tw.vehicle.document.receipt.cancel.line', 'cancel_id', 'Cancel Lines')
    available_lot_ids = fields.Many2many('stock.lot', string='Domain Lot', compute='_compute_available_lot_ids')
    available_receipt_ids = fields.Many2many(
        'tw.vehicle.registration.receipt',
        string='Available Receipts',
        compute='_compute_available_receipt_ids'
    )

    # Compute Methods
    @api.depends('company_id')
    def _compute_available_receipt_ids(self):
        """Compute available registration receipts that have cancellable lots."""
        for record in self:
            available_receipts = []
            
            if record.company_id:
                # Query for receipts with cancellable lots
                self._cr.execute("""
                    SELECT DISTINCT r.id
                    FROM tw_vehicle_registration_receipt r
                    INNER JOIN tw_vehicle_registration_receipt_line rl ON rl.vehicle_registration_receipt_id = r.id
                    INNER JOIN stock_lot sl ON sl.id = rl.lot_id
                    WHERE r.company_id = %s
                    AND r.state = 'done'
                    AND rl.state != 'cancel'
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tw_vehicle_document_receipt_cancel_line cl
                        JOIN tw_vehicle_document_receipt_cancel c ON cl.cancel_id = c.id
                        LEFT JOIN tw_cancellation tc ON c.cancellation_id = tc.id
                        WHERE cl.lot_id = sl.id 
                        AND tc.state != 'confirmed'
                        AND c.id != %s
                    )
                """, (record.company_id.id, record.id or 0))
                available_receipts = [row[0] for row in self._cr.fetchall()]
            
            record.available_receipt_ids = [(6, 0, available_receipts)]
    
    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if hasattr(models, 'NewId') and isinstance(rec.id, models.NewId) or not rec.id:
                    rec.name = 'New'
                    continue
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('CPNS', str(rec.company_id.code))

    @api.depends('vehicle_document_receipt_id')
    def _compute_available_lot_ids(self):
        for rec in self:
            rec.available_lot_ids = False
            if rec.vehicle_document_receipt_id:
                # Get lots from receipt lines that aren't already in other cancellations
                query = """
                    SELECT DISTINCT rl.lot_id 
                    FROM tw_vehicle_registration_receipt_line rl
                    JOIN stock_lot sl ON rl.lot_id = sl.id
                    WHERE rl.vehicle_registration_receipt_id = %s
                    AND rl.state != 'cancel'
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tw_vehicle_document_receipt_cancel_line cl
                        JOIN tw_vehicle_document_receipt_cancel c ON cl.cancel_id = c.id
                        LEFT JOIN tw_cancellation tc ON c.cancellation_id = tc.id
                        WHERE cl.lot_id = rl.lot_id 
                        AND tc.state != 'confirmed'
                        AND c.id != %s
                    )
                """
                self._cr.execute(query, (rec.vehicle_document_receipt_id.id, rec.id or 0))
                lot_ids = [row[0] for row in self._cr.fetchall()]
                rec.available_lot_ids = [(6, 0, lot_ids)] if lot_ids else False

    # Onchange Methods
    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.vehicle_document_receipt_id = False
        
    @api.onchange('vehicle_document_receipt_id')
    def _onchange_vehicle_document_receipt_id(self):
        self.transaction_name = False
        self.cancel_line_ids = False
        if self.vehicle_document_receipt_id:
            self.transaction_name = self.vehicle_document_receipt_id.name
    
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You cannot delete a cancellation that is not in draft or cancelled state.'))
        return super().unlink()
    
    # Action Methods
    def action_confirm(self):
        """Confirm cancellation — only reverses documents received in the selected transaction."""
        self._validity_check()
        selected_receipt = self.vehicle_document_receipt_id

        for line in self.cancel_line_ids:
            lot = line.lot_id
            receipt_line = selected_receipt.vehicle_registration_receipt_line_ids.filtered(
                lambda l: l.lot_id == lot and l.state != 'cancel'
            )
            if not receipt_line:
                continue

            # Only cancel STNK if it was received in the selected transaction
            if lot.vehicle_registration_receipt_id and lot.vehicle_registration_receipt_id.id == selected_receipt.id:
                receipt_line.action_registration_receipt_cancel()

            # Only cancel Notice if it was received in the selected transaction
            if lot.notice_receipt_id and lot.notice_receipt_id.id == selected_receipt.id:
                receipt_line.action_notice_receipt_cancel()

            # Only cancel Plate if it was received in the selected transaction
            if lot.plate_receipt_id and lot.plate_receipt_id.id == selected_receipt.id:
                receipt_line.action_plate_receipt_cancel()

            # Mark receipt line as cancelled when at least one doc was reversed
            if receipt_line.state != 'cancel':
                receipt_line.suspend_security().write({'state': 'cancel'})

        # Cancel the receipt header if no active lines remain
        if (selected_receipt and
                not selected_receipt.vehicle_registration_receipt_line_ids.filtered(lambda l: l.state != 'cancel')):
            selected_receipt.action_cancel()

        return self.cancellation_id.action_confirm()

    # Validation Methods
    def _validity_check(self):
        for rec in self:
            if not rec.vehicle_document_receipt_id:
                continue

            if not rec.cancel_line_ids:
                raise ValidationError(_('Please add at least one lot to cancel.'))

            # Check for duplicate lots
            cancel_lots = rec.cancel_line_ids.mapped('lot_id')
            if len(cancel_lots) != len(set(cancel_lots)):
                raise ValidationError(_('Duplicate lots found. Please remove duplicates.'))

            # Check receipt state
            if rec.vehicle_document_receipt_id.state == 'cancel':
                raise ValidationError(_('This receipt is already cancelled.'))

            # Check if lots are in receipt
            receipt_lots = rec.vehicle_document_receipt_id.vehicle_registration_receipt_line_ids.mapped('lot_id')
            
            invalid_lots = rec.cancel_line_ids.filtered(
                lambda l: l.lot_id not in receipt_lots
            )
            if invalid_lots:
                raise ValidationError(_('Some lots are not in the selected receipt.'))
    
    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)

    def action_request_approval(self):
        return super().action_request_approval(value=5)

    def validate_order(self):
        self.ensure_one()
        self._validity_check()
        return super().validate_order()
