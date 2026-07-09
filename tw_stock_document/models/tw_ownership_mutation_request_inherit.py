# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class TwOwnershipMutationRequestStockDoc(models.Model):
    """Inherit tw.ownership.mutation.request to add stock_document_ids for selection domain"""
    _inherit = "tw.ownership.mutation.request"
    
    # Stock documents for selection domain (via inheritance - to avoid circular dependency)
    stock_document_ids = fields.Many2many(
        comodel_name='tw.stock.document',
        relation='tw_ownership_mutation_request_stock_doc_rel',
        column1='request_id',
        column2='stock_document_id',
        compute='_compute_stock_document_ids',
        string='Stock Documents',
        store=False
    )
    
    @api.depends('company_id', 'bpkb_source_location_id')
    def _compute_stock_document_ids(self):
        """Compute available stock documents for selection based on branch and location"""
        for record in self:
            if not record.company_id or not record.bpkb_source_location_id:
                record.stock_document_ids = False
                continue
            
            # Find stock documents that:
            # - Belong to the same branch
            # - Are BPKB type
            # - Are in 'stock' state
            # - Match the source location
            # - Not already in another pending request
            query = """
                SELECT sd.id 
                FROM tw_stock_document sd
                WHERE sd.company_id = %s
                AND sd.type = 'bpkb'
                AND sd.state = 'stock'
                AND sd.location_id = %s
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_ownership_mutation_request_line orl
                    JOIN tw_ownership_mutation_request orm ON orl.ownership_mutation_request_id = orm.id
                    WHERE orl.stock_document_id = sd.id 
                    AND orm.state NOT IN ('done', 'cancel')
                    AND orm.id != %s
                )
            """
            
            self._cr.execute(query, (record.company_id.id, record.bpkb_source_location_id.id, record.id or 0))
            doc_ids = [row[0] for row in self._cr.fetchall()]
            record.stock_document_ids = [(6, 0, doc_ids)] if doc_ids else False
    
    def _create_outgoing_mutation(self):
        """Override to include stock_document_id in outgoing mutation lines."""
        # Call parent method first
        outgoing = super()._create_outgoing_mutation()
        
        # Update mutation lines with stock_document_id from request lines
        for i, request_line in enumerate(self.ownership_mutation_request_line_ids):
            if hasattr(request_line, 'stock_document_id') and request_line.stock_document_id:
                # Find the corresponding mutation line by lot_id
                for mutation_line in outgoing.document_mutation_line_ids:
                    if mutation_line.lot_id.id == request_line.lot_id.id:
                        mutation_line.stock_document_id = request_line.stock_document_id.id
                        break
        
        return outgoing
