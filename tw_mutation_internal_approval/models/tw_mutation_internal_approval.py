# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from datetime import datetime
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockPickingAsset(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "tw.approval.mixin"]


    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('confirmed',)
    ], string="Status")


    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Table Approval", domain=[('model_id', '=', _inherit)])
    is_approval = fields.Boolean(string='Need Approval', compute="_compute_is_approval", store=True, help='This fields used for domain / attributes')
    
    # 9: relation fields
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('location_id', 'location_dest_id')
    def _compute_is_approval(self):
        self.is_approval = False
        for record in self:
            if record.location_id.is_approval or record.location_dest_id.is_approval:
                record.is_approval = True
                
    # 12: override methods
    
    # 13: action methods
    def action_rfa(self):
        if not self.picking_line_ids:
            raise Warning("Perhatian!\nTab Line tidak boleh kosong!")
        
        value = 0
        for picking_line in self.picking_line_ids:
            if picking_line.quantity > picking_line.qty_available:
                raise Warning("Perhatian!\nQty yang dimasukkan tidak boleh lebih besar dari Qty Available!")
            value += picking_line.quantity
        
        return super().action_request_approval(value=value)
        