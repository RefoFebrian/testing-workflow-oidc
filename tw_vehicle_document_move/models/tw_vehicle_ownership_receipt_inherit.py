# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _


class TwVehicleOwnershipReceiptInherit(models.Model):
    _inherit = "tw.vehicle.ownership.receipt"

    def action_confirm(self):
        """Override to create document move tracking after confirmation"""
        res = super(TwVehicleOwnershipReceiptInherit, self).action_confirm()
        
        # Create document move for each BPKB received
        move_model = self.env['tw.vehicle.document.move']
        for rec in self.filtered(lambda r: r.state == 'done'):
            for line in rec.vehicle_ownership_receipt_line_ids:
                move_model._create_document_move({
                    'reference': rec.name,
                    'date': rec.date,
                    'document_type': 'vehicle_ownership',
                    'document_number': line.vehicle_ownership_number,
                    'lot_id': line.lot_id.id,
                    'destination_location_id': rec.vehicle_ownership_location_id.id,
                    'company_id': rec.company_id.id,
                })
        
        return res

    def action_cancel(self):
        """Override to create document move tracking on cancel (BPKB receipt)"""
        move_model = self.env['tw.vehicle.document.move']
        for rec in self.filtered(lambda r: r.state == 'done'):
            for line in rec.vehicle_ownership_receipt_line_ids:
                if line.vehicle_ownership_number:
                    move_model._create_document_move({
                        'reference': f"{rec.name} (CANCEL)",
                        'date': fields.Date.context_today(self),
                        'document_type': 'vehicle_ownership',
                        'document_number': line.vehicle_ownership_number,
                        'lot_id': line.lot_id.id,
                        'source_location_id': line.lot_id.vehicle_ownership_location_id.id,
                        # destination kosong - dokumen kembali ke intransit
                        'company_id': rec.company_id.id,
                    })

        return super(TwVehicleOwnershipReceiptInherit, self).action_cancel()
