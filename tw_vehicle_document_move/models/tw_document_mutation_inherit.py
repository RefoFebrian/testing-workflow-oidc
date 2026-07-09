# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _


class TwDocumentMutationInherit(models.Model):
    _inherit = "tw.document.mutation"

    def action_confirm(self):
        """Override to create document move tracking after confirmation"""
        res = super(TwDocumentMutationInherit, self).action_confirm()
        
        # Create document move for each mutation line
        move_model = self.env['tw.vehicle.document.move']
        for rec in self.filtered(lambda r: r.state == 'done'):
            for line in rec.document_mutation_line_ids:
                # Note: tw.document.mutation uses 'stnk'/'bpkb' values
                # but tw.vehicle.document.move uses 'vehicle_registration'/'vehicle_ownership'
                if rec.document_type == 'stnk':
                    move_model._create_document_move({
                        'reference': rec.name,
                        'date': rec.date,
                        'document_type': 'vehicle_registration',  # Map stnk -> vehicle_registration
                        'document_number': line.lot_id.vehicle_registration_number,
                        'lot_id': line.lot_id.id,
                        'source_location_id': rec.stnk_source_location_id.id,
                        'destination_location_id': rec.stnk_dest_location_id.id,
                        'company_id': rec.company_id.id,
                    })
                else:  # bpkb
                    move_model._create_document_move({
                        'reference': rec.name,
                        'date': rec.date,
                        'document_type': 'vehicle_ownership',  # Map bpkb -> vehicle_ownership
                        'document_number': line.lot_id.vehicle_ownership_number,
                        'lot_id': line.lot_id.id,
                        'source_location_id': rec.bpkb_source_location_id.id,
                        'destination_location_id': rec.bpkb_dest_location_id.id,
                        'company_id': rec.company_id.id,
                    })
        
        return res
