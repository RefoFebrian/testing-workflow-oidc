# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAccountStockInboundInherit(models.Model):
    _inherit = "tw.stock.inbound"
    _description = "Stock Inbound"
    
    # 7: defaults methods

    # 8: fields
    move_count = fields.Integer(
        string='Journal Entries Count',
        compute='_compute_move_count'
    )

    # 9: relation fields
    volume = fields.Float(string="Volume", default=0.0)

    # 9: relation fields
    pricelist_type_id = fields.Many2one(comodel_name='tw.selection', string='Pricelist Type', domain=[('type', '=', 'PricelistCategory')], help="Pricelist that can be used for supplier cost.")
    invoice_id = fields.Many2one(comodel_name='account.move', string='Invoice Expedition')
    move_ids = fields.Many2many(
        comodel_name='account.move',
        string='Journal Entries',
        help='Journal entries created for expedition cost'
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('move_ids')
    def _compute_move_count(self):
        for record in self:
            record.move_count = len(record.move_ids)

    @api.onchange('stock_inbound_id')
    def onchange_stock_inbound_id(self):
        if self.stock_inbound_id:
            self.pricelist_type_id = self.stock_inbound_id.pricelist_type_id.id
            self.volume = self.stock_inbound_id.volume

    # 12: override methods

    # 13: action methods
    def action_view_moves(self):
        """Smart button action to view expedition journal entries."""
        self.ensure_one()
        action = {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.move_ids.ids)],
            'context': {'create': False},
        }
        if len(self.move_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.move_ids.id
        return action

    # 14: private methods
    

