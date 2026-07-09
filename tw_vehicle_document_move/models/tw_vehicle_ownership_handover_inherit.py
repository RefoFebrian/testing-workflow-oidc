# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError as Warning

class TwVehicleOwnershipHandoverInherit(models.Model):
    _inherit = "tw.vehicle.ownership.handover"

    def action_confirm(self):
        """Override to create document move tracking after confirmation"""
        # Create document move for BPKB handover
        move_model = self.env['tw.vehicle.document.move']
        for rec in self:
            for line in rec.ownership_handover_line_ids:
                move_model._create_document_move({
                    'reference': rec.name,
                    'date': rec.date,
                    'document_type': 'vehicle_ownership',
                    'document_number': line.lot_id.vehicle_ownership_number,
                    'lot_id': line.lot_id.id,
                    'source_location_id': line.lot_id.vehicle_ownership_location_id.id,
                    # destination is empty for customer handover
                    'company_id': rec.company_id.id,
                })
        try:
            res = super(TwVehicleOwnershipHandoverInherit, self).action_confirm()
        except Exception as e:
            raise Warning(_("Failed to confirm handover: %s") % str(e))
        
        return res

    def action_cancel(self):
        """Override to create document move tracking on cancel (BPKB handover)"""
        move_model = self.env['tw.vehicle.document.move']
        for rec in self.filtered(lambda r: r.state == 'cancel' or r.state == 'done'):
            for line in rec.ownership_handover_line_ids:
                if line.lot_id.vehicle_ownership_number:
                    move_model._create_document_move({
                        'reference': f"{rec.name} (CANCEL)",
                        'date': fields.Date.context_today(self),
                        'document_type': 'vehicle_ownership',
                        'document_number': line.lot_id.vehicle_ownership_number,
                        'lot_id': line.lot_id.id,
                        # destination = lokasi BPKB di branch (dikembalikan dari customer)
                        'destination_location_id': line.lot_id.vehicle_ownership_location_id.id,
                        'company_id': rec.company_id.id,
                    })

        return super(TwVehicleOwnershipHandoverInherit, self).action_cancel()