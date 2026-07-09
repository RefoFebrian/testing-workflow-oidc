# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError as Warning

class TwVehicleRegistrationHandoverInherit(models.Model):
    _inherit = "tw.vehicle.registration.handover"

    def action_confirm(self):
        """Override to create document move tracking after confirmation"""
        # Create document move for STNK handover
        move_model = self.env['tw.vehicle.document.move']
        for rec in self:
            for line in rec.registration_handover_line_ids:
                if line.stnk_handover_date and not line.lot_id.registration_handover_id:
                    move_model._create_document_move({
                        'reference': rec.name,
                        'date': rec.date,
                        'document_type': 'vehicle_registration',
                        'document_number': line.lot_id.vehicle_registration_number,
                        'lot_id': line.lot_id.id,
                        'source_location_id': line.lot_id.vehicle_registration_location_id.id,
                        # destination is empty for customer handover
                        'company_id': rec.company_id.id,
                    })

        try:    
            res = super(TwVehicleRegistrationHandoverInherit, self).action_confirm()
        except Exception as e:
            raise Warning(_("Failed to confirm handover: %s") % str(e))
        
        return res

    def action_cancel(self):
        """Override to create document move tracking on cancel (STNK handover)"""
        move_model = self.env['tw.vehicle.document.move']
        for rec in self.filtered(lambda r: r.state == 'cancel' or r.state == 'done'):
            for line in rec.registration_handover_line_ids:
                if line.lot_id.vehicle_registration_number:
                    move_model._create_document_move({
                        'reference': f"{rec.name} (CANCEL)",
                        'date': fields.Date.context_today(self),
                        'document_type': 'vehicle_registration',
                        'document_number': line.lot_id.vehicle_registration_number,
                        'lot_id': line.lot_id.id,
                        # destination = lokasi STNK di branch (dikembalikan dari customer)
                        'destination_location_id': line.lot_id.vehicle_registration_location_id.id,
                        'company_id': rec.company_id.id,
                    })

        return super(TwVehicleRegistrationHandoverInherit, self).action_cancel()
