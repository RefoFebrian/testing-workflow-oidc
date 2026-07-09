# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwVehicleRegistrationReceiptInherit(models.Model):
    """
    Inherit tw.vehicle.registration.receipt to create tw.stock.document
    when confirming STNK receipt (PST).
    """
    _inherit = "tw.vehicle.registration.receipt"

    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods

    # 12: override methods
    def action_confirm(self):
        """Override to create stock document for STNK on confirm"""
        res = super().action_confirm()
        
        stock_doc_model = self.env['tw.stock.document']
        for rec in self.filtered(lambda r: r.state == 'done'):
            for line in rec.vehicle_registration_receipt_line_ids:
                # Only process if STNK is being received (has number and not already received)
                if line.vehicle_registration_number:
                    existing = stock_doc_model.suspend_security().search([
                        ('lot_id', '=', line.lot_id.id),
                        ('type', '=', 'stnk'),
                    ], limit=1)
                    if existing:
                        # Re-activate existing record (e.g. previously cancelled)
                        existing.suspend_security().write({
                            'state': 'stock',
                            'location_id': rec.vehicle_registration_location_id.id,
                            'document_number': line.vehicle_registration_number,
                            'company_id': rec.company_id.id,
                        })
                    else:
                        stock_doc_model.suspend_security().create({
                            'lot_id': line.lot_id.id,
                            'type': 'stnk',
                            'state': 'stock',
                            'location_id': rec.vehicle_registration_location_id.id,
                            'document_number': line.vehicle_registration_number,
                            'company_id': rec.company_id.id,
                        })
        
        return res

    def action_cancel(self):
        """Override to cancel stock document on receipt cancellation."""
        res = super().action_cancel()
        
        stock_doc_model = self.env['tw.stock.document']
        for rec in self.filtered(lambda r: r.state == 'cancel'):
            for line in rec.vehicle_registration_receipt_line_ids:
                stock_doc = stock_doc_model.suspend_security().search([
                    ('lot_id', '=', line.lot_id.id),
                    ('type', '=', 'stnk'),
                ], limit=1)
                if stock_doc:
                    stock_doc.action_cancel_receipt()
        
        return res

    # 13: action methods
    
    # 14: private methods
