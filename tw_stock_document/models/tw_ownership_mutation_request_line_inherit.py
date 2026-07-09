# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class TwOwnershipMutationRequestLineStockDoc(models.Model):
    """Inherit tw.ownership.mutation.request.line to add stock_document_id selection"""
    _inherit = "tw.ownership.mutation.request.line"
    
    # Stock document selection (via inheritance - to avoid circular dependency)
    stock_document_id = fields.Many2one(
        'tw.stock.document',
        string='BPKB Document',
        help='Select BPKB document from stock document'
    )
    
    @api.onchange('stock_document_id')
    def _onchange_stock_document_id(self):
        """Set lot_id from stock_document_id"""
        for line in self:
            if line.stock_document_id:
                line.lot_id = line.stock_document_id.lot_id
