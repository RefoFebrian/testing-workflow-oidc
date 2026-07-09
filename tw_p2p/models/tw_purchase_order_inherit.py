# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwP2pPurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = 'Purchase Order'

    # 7: defaults methods

    # 8: fields
    state = fields.Selection(selection_add=[
        ('confirmed','Confirmed'),
        ('purchase',),
    ])

    # Audit Trail
    confirm_date = fields.Datetime(string='Confirmed on')
    confirm_uid = fields.Many2one('res.users', string="Confirmed by")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('division','state','origin')
    def _compute_is_invisible_button(self):
        for order in self:
            order.is_invisible_button = False
            if order.origin and 'P2P' in order.origin:
                order.is_invisible_button = True

    # 12: override methods
    def _create_picking(self):
        for order in self:
            check_p2p_transaction = self.env['tw.p2p.purchase.order'].search([('purchase_order_id','=',order.id)])
            if order.origin and check_p2p_transaction:
                return True

        return super(TwP2pPurchaseOrder,self)._create_picking()

    # 13: action methods
    def button_confirm(self):
        check_p2p_transaction = self.env['tw.p2p.purchase.order'].search([('purchase_order_id','=',self.id)])
        if self.origin and check_p2p_transaction:
            return self.write({
                'state': 'confirmed',
                'confirm_uid': self._uid,
                'confirm_date': datetime.now()
            })

        return super(TwP2pPurchaseOrder,self).button_confirm()

    def action_create_invoice(self):
        for order in self:
            check_p2p_transaction = self.env['tw.p2p.purchase.order'].search([('purchase_order_id','=',order.id)])
            if order.origin and check_p2p_transaction:
                return True
        return super(TwP2pPurchaseOrder,self).action_create_invoice()

    def action_view_p2p(self):
        """Action to view the related P2P Purchase Order"""
        self.ensure_one()
        p2p = self.env['tw.p2p.purchase.order'].search([('name', '=', self.origin)], limit=1)
        if p2p:
            return {
                'name': 'P2P Purchase Order',
                'type': 'ir.actions.act_window',
                'res_model': 'tw.p2p.purchase.order',
                'view_mode': 'form',
                'res_id': p2p.id,
                'target': 'current',
            }
        
    # 14: private methods


