# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwVehicleOwnershipReceiptInherit(models.Model):
    """
    Inherit tw.vehicle.ownership.receipt to create tw.stock.document
    when confirming BPKB receipt (PSB).
    """
    _inherit = "tw.vehicle.ownership.receipt"

    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods

    # 12: override methods
    def action_confirm(self):
        """Override to create stock document for BPKB on confirm"""
        res = super().action_confirm()
        
        stock_doc_model = self.env['tw.stock.document']
        for rec in self.filtered(lambda r: r.state == 'done'):
            # Tentukan branch dan lokasi final untuk stock document
            target_company_id = rec.dest_company_id.id if rec.is_for_other_branch and rec.dest_company_id else rec.company_id.id
            target_location_id = rec.dest_ownership_location_id.id if rec.is_for_other_branch and rec.dest_ownership_location_id else rec.vehicle_ownership_location_id.id

            for line in rec.vehicle_ownership_receipt_line_ids:
                # Only process if BPKB is being received (has number and not already received)
                if line.vehicle_ownership_number:
                    existing = stock_doc_model.suspend_security().search([
                        ('lot_id', '=', line.lot_id.id),
                        ('type', '=', 'bpkb'),
                    ], limit=1)
                    if existing:
                        # Re-activate existing record (e.g. previously cancelled)
                        existing.suspend_security().write({
                            'state': 'stock',
                            'location_id': target_location_id,
                            'document_number': line.vehicle_ownership_number,
                            'company_id': target_company_id,
                        })
                    else:
                        stock_doc_model.suspend_security().create({
                            'lot_id': line.lot_id.id,
                            'type': 'bpkb',
                            'state': 'stock',
                            'location_id': target_location_id,
                            'document_number': line.vehicle_ownership_number,
                            'company_id': target_company_id,
                        })
        
        return res

    def action_cancel(self):
        """Override to cancel stock document on receipt cancellation."""
        res = super().action_cancel()
        
        stock_doc_model = self.env['tw.stock.document']
        for rec in self.filtered(lambda r: r.state == 'cancel'):
            for line in rec.vehicle_ownership_receipt_line_ids:
                stock_doc = stock_doc_model.suspend_security().search([
                    ('lot_id', '=', line.lot_id.id),
                    ('type', '=', 'bpkb'),
                ], limit=1)
                if stock_doc:
                    stock_doc.action_cancel_receipt()
        
        return res

    # 13: action methods
    
    # 14: private methods
