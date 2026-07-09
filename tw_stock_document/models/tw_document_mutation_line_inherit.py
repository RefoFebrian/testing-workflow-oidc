# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class TwDocumentMutationLineStockDoc(models.Model):
    """Inherit tw.document.mutation.line to add stock_document_id selection"""
    _inherit = "tw.document.mutation.line"
    
    # Stock document selection (via inheritance - to avoid circular dependency)
    stock_document_id = fields.Many2one(
        'tw.stock.document',
        string='Document',
        help='Select BPKB/STNK document from stock document'
    )
    
    # Current location from stock document (single field to replace stnk/bpkb location)
    current_location_id = fields.Many2one(
        'tw.vehicle.document.location',
        string='Current Location',
        related='stock_document_id.location_id',
        readonly=True,
        store=False
    )
    
    @api.onchange('stock_document_id')
    def _onchange_stock_document_id(self):
        """Set lot_id from stock_document_id"""
        for line in self:
            if line.stock_document_id:
                line.lot_id = line.stock_document_id.lot_id

