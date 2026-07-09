# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockLotInherit(models.Model):
    _inherit = "stock.lot"

    vehicle_document_move_ids = fields.One2many(
        comodel_name='tw.vehicle.document.move',
        inverse_name='lot_id',
        string='Document Moves'
    )
    
    vehicle_document_move_count = fields.Integer(
        string='Document Move Count',
        compute='_compute_vehicle_document_move_count',
        store=True
    )

    @api.depends('vehicle_document_move_ids')
    def _compute_vehicle_document_move_count(self):
        for lot in self:
            lot.vehicle_document_move_count = len(lot.vehicle_document_move_ids)

    def action_view_vehicle_document_moves(self):
        self.ensure_one()
        action = {
            'name': _('Vehicle Document Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.vehicle.document.move',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {
                'default_lot_id': self.id,
                'default_company_id': self.company_id.id,
                'search_default_group_by_type': 1,  # Default grouping by document_type
            },
        }
        return action
