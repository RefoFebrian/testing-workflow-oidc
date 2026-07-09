# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwVehicleRegistrationHandoverInherit(models.Model):
    """
    Inherit tw.vehicle.registration.handover to update tw.stock.document
    state to 'customer' when handing over STNK.
    """
    _inherit = "tw.vehicle.registration.handover"

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
            for line in rec.registration_handover_line_ids:
                # Update STNK stock document to customer state when STNK is handed over
                if line.stnk_handover_date:
                    stock_doc = stock_doc_model.suspend_security().search([
                        ('lot_id', '=', line.lot_id.id),
                        ('type', '=', 'stnk'),
                    ], limit=1)
                    if stock_doc and stock_doc.state != 'customer':
                        stock_doc.action_set_customer()
        
        return res

    def action_cancel(self):
        """Override to restore stock document state to stock on cancel"""
        res = super().action_cancel()
        
        stock_doc_model = self.env['tw.stock.document']
        for rec in self.filtered(lambda r: r.state == 'cancel'):
            for line in rec.registration_handover_line_ids:
                if line.stnk_handover_date:
                    stock_doc = stock_doc_model.suspend_security().search([
                        ('lot_id', '=', line.lot_id.id),
                        ('type', '=', 'stnk'),
                    ], limit=1)
                    if stock_doc and stock_doc.state == 'customer':
                        # Restore to stock, location NOT changed
                        stock_doc.action_set_stock()
        
        return res

    # 13: action methods
    
    # 14: private methods
