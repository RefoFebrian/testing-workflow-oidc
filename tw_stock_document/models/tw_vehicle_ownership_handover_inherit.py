# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwVehicleOwnershipHandoverInherit(models.Model):
    """
    Inherit tw.vehicle.ownership.handover to update tw.stock.document
    state to 'customer' when handing over BPKB.
    """
    _inherit = "tw.vehicle.ownership.handover"

    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods

    # 12: override methods
    def action_confirm(self):
        """Override to update stock document state to customer on confirm"""
        res = super().action_confirm()
        
        stock_doc_model = self.env['tw.stock.document']
        for rec in self.filtered(lambda r: r.state == 'done'):
            for line in rec.ownership_handover_line_ids:
                # Update BPKB stock document to customer state when BPKB is handed over
                if line.ownership_handover_date:
                    stock_doc = stock_doc_model.suspend_security().search([
                        ('lot_id', '=', line.lot_id.id),
                        ('type', '=', 'bpkb'),
                    ], limit=1)
                    if stock_doc and stock_doc.state != 'customer':
                        stock_doc.action_set_customer()
        
        return res

    def action_cancel(self):
        """Override to restore stock document state to stock on cancel"""
        res = super().action_cancel()
        
        stock_doc_model = self.env['tw.stock.document']
        for rec in self.filtered(lambda r: r.state == 'cancel'):
            for line in rec.ownership_handover_line_ids:
                if line.ownership_handover_date:
                    stock_doc = stock_doc_model.suspend_security().search([
                        ('lot_id', '=', line.lot_id.id),
                        ('type', '=', 'bpkb'),
                    ], limit=1)
                    if stock_doc and stock_doc.state == 'customer':
                        # Restore to stock, location NOT changed
                        stock_doc.action_set_stock()
        
        return res

    # 13: action methods
    
    # 14: private methods
