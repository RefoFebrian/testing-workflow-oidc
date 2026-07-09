# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwDocumentMutationInherit(models.Model):
    """
    Inherit tw.document.mutation to:
    1. Add domain based on tw.stock.document state='stock'
    2. Update location in tw.stock.document on confirm
    """
    _inherit = "tw.document.mutation"

    # 7: defaults methods
    
    # 8: fields
    
    # 9: relation fields
    # Override domain_lot_ids to use tw.stock.document
    domain_lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        string='Domain Lot',
        compute='_compute_domain_lot_ids_stock_doc',
        store=False,
    )
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('company_id', 'document_type', 'stnk_source_location_id', 'bpkb_source_location_id')
    def _compute_domain_lot_ids_stock_doc(self):
        """Override to use tw.stock.document for domain selection with state='stock'"""
        for rec in self:
            if not rec.company_id or not rec.document_type:
                rec.domain_lot_ids = False
                continue

            # Determine document type and source location
            if rec.document_type == 'stnk':
                if not rec.stnk_source_location_id:
                    rec.domain_lot_ids = False
                    continue
                doc_type = 'stnk'
                source_location_id = rec.stnk_source_location_id.id
            else:  # bpkb
                if not rec.bpkb_source_location_id:
                    rec.domain_lot_ids = False
                    continue
                doc_type = 'bpkb'
                source_location_id = rec.bpkb_source_location_id.id

            # Query tw.stock.document with state='stock'
            query = """
                SELECT sd.lot_id 
                FROM tw_stock_document sd
                JOIN stock_lot sl ON sl.id = sd.lot_id
                WHERE sd.company_id = %s
                AND sd.type = %s
                AND sd.state = 'stock'
                AND sd.location_id = %s
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_document_mutation_line dml
                    JOIN tw_document_mutation dm ON dml.mutation_id = dm.id
                    WHERE dml.lot_id = sd.lot_id 
                    AND dm.state NOT IN ('done', 'cancel')
                    AND dm.document_type = %s
                    AND dm.id != %s
                )
            """
            params = (rec.company_id.id, doc_type, source_location_id, doc_type, rec.id or 0)
            self._cr.execute(query, params)
            lot_ids = [row[0] for row in self._cr.fetchall()]
            
            rec.domain_lot_ids = [(6, 0, lot_ids)] if lot_ids else False

    # 12: override methods
    def action_confirm(self):
        """Override to update tw.stock.document state and location on confirm.
        
        - internal: update location → state=done
        - outgoing: stock.doc → intransit + location=transit (company stays in Branch A)
        - incoming: stock.doc → stock + location=dest + company=Branch B
        """
        res = super().action_confirm()
        
        stock_doc_model = self.env['tw.stock.document']
        
        # Internal: update location in stock.document
        for rec in self.filtered(lambda r: r.state == 'done' and r.transfer_type == 'internal'):
            dest_location_id = rec.stnk_dest_location_id.id if rec.document_type == 'stnk' else rec.bpkb_dest_location_id.id
            doc_type = rec.document_type  # 'stnk' or 'bpkb'
            for line in rec.document_mutation_line_ids:
                stock_doc = stock_doc_model.suspend_security().search([
                    ('lot_id', '=', line.lot_id.id),
                    ('type', '=', doc_type),
                ], limit=1)
                if stock_doc:
                    stock_doc.suspend_security().write({'location_id': dest_location_id})
        
        # Outgoing: update stock.doc → intransit + location=transit (company unchanged)
        for rec in self.filtered(lambda r: r.state == 'confirmed' and r.transfer_type == 'outgoing'):
            doc_type = rec.document_type
            for line in rec.document_mutation_line_ids:
                stock_doc = stock_doc_model.suspend_security().search([
                    ('lot_id', '=', line.lot_id.id),
                    ('type', '=', doc_type),
                ], limit=1)
                if stock_doc:
                    stock_doc.suspend_security().write({
                        'state': 'intransit',
                        'location_id': rec.transit_location_id.id,
                        # company_id tetap Branch A — belum pindah
                    })
        
        # Incoming: update stock.doc → stock + location=dest + company=Branch B
        for rec in self.filtered(lambda r: r.state == 'done' and r.transfer_type == 'incoming'):
            doc_type = rec.document_type
            dest_location_id = rec.bpkb_dest_location_id.id if doc_type == 'bpkb' else rec.stnk_dest_location_id.id
            for line in rec.document_mutation_line_ids:
                stock_doc = stock_doc_model.suspend_security().search([
                    ('lot_id', '=', line.lot_id.id),
                    ('type', '=', doc_type),
                ], limit=1)
                if stock_doc:
                    stock_doc.suspend_security().write({
                        'state': 'stock',
                        'location_id': dest_location_id,
                        'company_id': rec.company_id.id,  # Pindah ke Branch B
                    })
        
        return res


    def _prepare_incoming_mutation_vals(self):
        """Override to include stock_document_id in incoming mutation lines."""
        vals = super()._prepare_incoming_mutation_vals()
        
        # Update mutation lines to include stock_document_id
        updated_lines = []
        for i, line in enumerate(self.document_mutation_line_ids):
            line_vals = vals['document_mutation_line_ids'][i][2] if i < len(vals.get('document_mutation_line_ids', [])) else {}
            
            # Add stock_document_id if it exists on the source line
            if hasattr(line, 'stock_document_id') and line.stock_document_id:
                line_vals['stock_document_id'] = line.stock_document_id.id
            
            updated_lines.append((0, 0, {
                'lot_id': line.lot_id.id,
                'stock_document_id': line.stock_document_id.id if hasattr(line, 'stock_document_id') and line.stock_document_id else False,
            }))
        
        vals['document_mutation_line_ids'] = updated_lines
        return vals

    # 13: action methods
    
    # 14: private methods

