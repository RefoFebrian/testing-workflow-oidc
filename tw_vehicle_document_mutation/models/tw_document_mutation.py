from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class TwDocumentMutation(models.Model):
    _name = "tw.document.mutation"
    _description = "Document Mutation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # 8: Fields
    name = fields.Char(string='Reference', required=True, readonly=True, copy=False, default='New', compute='_compute_name', store=True, tracking=True)
    note = fields.Text(string='Notes')
    date = fields.Date(string='Date', default=fields.Date.today)

    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),  # For outgoing that has been confirmed
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],string='Status',default='draft',tracking=True)
    
    document_type = fields.Selection(selection=[
            ('stnk', 'STNK'),
            ('bpkb', 'BPKB'),
        ],string='Document Type',required=True,tracking=True)
    
    transfer_type = fields.Selection(selection=[
            ('internal', 'Internal'),
            ('outgoing', 'Outgoing'),
            ('incoming', 'Incoming'),
        ],string='Transfer Type',default='internal',required=True,tracking=True)

    # Audit Trail
    # Confirm tracking (for outgoing)
    confirm_uid = fields.Many2one('res.users', string='Confirmed by')
    confirm_date = fields.Datetime(string='Confirmed on')
    
    # Done tracking
    done_uid = fields.Many2one('res.users', string='Done by')
    done_date = fields.Datetime(string='Done on')
    

    # 9: Relation Fields
    # Branch fields for inter-branch mutation
    destination_company_id = fields.Many2one(
        'res.company',
        string='Destination Branch',
        domain="[('parent_id', '!=', False), ('id', '!=', company_id)]",
        tracking=True
    )
    source_branch_id = fields.Many2one(
        'res.company',
        string='Source Branch',
        domain="[('parent_id', '!=', False), ('id', '!=', company_id)]",
        tracking=True
    )
    
    # Transit location for intransit state
    transit_location_id = fields.Many2one(
        'tw.vehicle.document.location',
        string='Transit Location',
        domain="[('type', '=', 'transit'), ('active', '=', True)]",
        tracking=True
    )
    
    # Outgoing ↔ Incoming relations
    outgoing_mutation_id = fields.Many2one(
        'tw.document.mutation',
        string='Outgoing Mutation',
        help='Reference to the outgoing mutation (for incoming records)'
    )
    incoming_mutation_id = fields.Many2one(
        'tw.document.mutation',
        string='Incoming Mutation',
        help='Reference to the created incoming mutation (for outgoing records)'
    )
    
    # Relation to Request BPKB
    ownership_mutation_request_id = fields.Many2one(
        'tw.ownership.mutation.request',
        string='Request BPKB'
    )
    
    company_id = fields.Many2one('res.company',string='Branch',required=True,default=lambda self: self.env.company,tracking=True)
    stnk_source_location_id = fields.Many2one('tw.vehicle.document.location',string='STNK Source Location',
        domain="[('company_id', '=', company_id), ('type', '=', 'internal'),('active', '=', True),('document_type', '=', 'vehicle_registration')]",
        tracking=True
    )
    stnk_dest_location_id = fields.Many2one('tw.vehicle.document.location',string='STNK Destination Location',
        domain="[('company_id', '=', company_id), ('type', '=', 'internal'),('active', '=', True), ('id', '!=', stnk_source_location_id),('document_type', '=', 'vehicle_registration')]",
        tracking=True
    )
    bpkb_source_location_id = fields.Many2one('tw.vehicle.document.location',string='BPKB Source Location',
        domain="[('company_id', '=', company_id), ('type', '=', 'internal'),('active', '=', True),('document_type', '=', 'vehicle_ownership')]",
        tracking=True
    )
    bpkb_dest_location_id = fields.Many2one('tw.vehicle.document.location',string='BPKB Destination Location',
        domain="[('company_id', '=', company_id), ('type', '=', 'internal'),('active', '=', True), ('id', '!=', bpkb_source_location_id),('document_type', '=', 'vehicle_ownership')]",
        tracking=True
    )
    
    
    domain_lot_ids = fields.Many2many('stock.lot', string='Domain Lot', compute='_compute_domain_lot_ids', store=False)
    document_mutation_line_ids = fields.One2many('tw.document.mutation.line','mutation_id',string='Mutation Lines')
    
    @api.depends('company_id','document_type','stnk_source_location_id','bpkb_source_location_id')
    def _compute_domain_lot_ids(self):
        for rec in self:
            if not rec.company_id or not rec.document_type and (rec.stnk_source_location_id or rec.bpkb_source_location_id):
                rec.domain_lot_ids = False
                continue

            # Build the base query
            query = """
                SELECT sl.id 
                FROM stock_lot sl
                LEFT JOIN tw_stock_document tsd on tsd.lot_id = sl.id and tsd.type = %s
                WHERE tsd.company_id = %s
            """
            params = [rec.document_type, rec.company_id.id]

            # Add document type specific conditions
            if rec.document_type == 'stnk':
                if not rec.stnk_source_location_id:
                    rec.domain_lot_ids = False
                    continue
                query += """
                    AND sl.vehicle_registration_receipt_id IS NOT NULL
                    AND sl.registration_handover_id IS NULL
                    AND sl.vehicle_registration_location_id = %s
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tw_document_mutation_line dml
                        JOIN tw_document_mutation dm ON dml.mutation_id = dm.id
                        WHERE dml.lot_id = sl.id 
                        AND dm.state NOT IN ('done', 'cancel')
                        AND dm.id != %s
                    )
                """
                params.extend([rec.stnk_source_location_id.id, rec.id or 0])
            else:  # bpkb
                if not rec.bpkb_source_location_id:
                    rec.domain_lot_ids = False
                    continue
                query += """
                    AND sl.vehicle_ownership_receipt_id IS NOT NULL
                    AND sl.ownership_handover_id IS NULL
                    AND sl.vehicle_ownership_location_id = %s
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tw_document_mutation_line dml
                        JOIN tw_document_mutation dm ON dml.mutation_id = dm.id
                        WHERE dml.lot_id = sl.id 
                        AND dm.state NOT IN ('done', 'cancel')
                        AND dm.id != %s
                    )
                """
                params.extend([rec.bpkb_source_location_id.id, rec.id or 0])

            # Execute the query and get the results
            self._cr.execute(query, tuple(params))
            lot_ids = [row[0] for row in self._cr.fetchall()]
            
            rec.domain_lot_ids = [(6, 0, lot_ids)] if lot_ids else False
    
    @api.depends('company_id', 'document_type', 'transfer_type')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if hasattr(models, 'NewId') and isinstance(rec.id, models.NewId) or not rec.id:
                    rec.name = 'New'
                    continue
                if rec.company_id and rec.document_type:
                    # Determine prefix based on transfer_type
                    if rec.transfer_type == 'outgoing':
                        prefix = 'MDO'  # Mutasi Dokumen Outgoing
                    elif rec.transfer_type == 'incoming':
                        prefix = 'MDI'  # Mutasi Dokumen Incoming
                    else:  # internal
                        prefix = 'MUS' if rec.document_type == 'stnk' else 'MUB'
                    rec.name = rec.env['ir.sequence'].get_sequence_code(prefix, str(rec.company_id.code))
    
    @api.onchange('company_id')
    def onchange_company_id(self):
        for rec in self:
            rec.document_mutation_line_ids = False
            rec.stnk_source_location_id = False
            rec.stnk_dest_location_id = False
            rec.bpkb_source_location_id = False
            rec.bpkb_dest_location_id = False
    
    @api.onchange('stnk_source_location_id','bpkb_source_location_id')
    def onchange_source_location_id(self):
        for rec in self:
            rec.stnk_dest_location_id = False
            rec.bpkb_dest_location_id = False
            rec.document_mutation_line_ids = False
    
    def action_confirm(self):
        """
        Confirm document mutation based on transfer_type:
        - internal: Update document locations and set state to done
        - outgoing: Create incoming mutation at destination branch, set state to confirmed
        - incoming: Complete inter-branch transfer, set state to done
        """
        for rec in self:
            rec._validate_document_mutation()
            
            if rec.transfer_type == 'internal':
                # Internal mutation - update locations and done
                self._confirm_internal(rec)
            elif rec.transfer_type == 'outgoing':
                # Outgoing mutation - create incoming at destination
                self._confirm_outgoing(rec)
            elif rec.transfer_type == 'incoming':
                # Incoming mutation - final step of inter-branch transfer
                self._confirm_incoming(rec)
    
    def _confirm_internal(self, rec):
        """Confirm internal mutation - update locations and set state to done."""
        for line in rec.document_mutation_line_ids:
            if rec.document_type == 'stnk':
                line.lot_id.suspend_security().write({
                    'vehicle_registration_location_id': rec.stnk_dest_location_id.id,
                })
            else:  # bpkb
                line.lot_id.suspend_security().write({
                    'vehicle_ownership_location_id': rec.bpkb_dest_location_id.id,
                })
        
        rec.suspend_security().write({
            'state': 'done',
            'done_uid': self.env.user.id,
            'done_date': datetime.now(),
        })
    
    def _confirm_outgoing(self, rec):
        """Confirm outgoing mutation — create incoming at destination branch.
        Update lot.vehicle_ownership_location_id to transit at this step.
        """
        if not rec.destination_company_id:
            raise UserError(_('Please select a destination branch for outgoing mutation.'))
        
        if not rec.transit_location_id:
            raise UserError(_('Please select a transit location.'))
        
        # Update lot location ke transit saat outgoing dikonfirmasi
        for line in rec.document_mutation_line_ids:
            line.lot_id.suspend_security().write({
                'vehicle_ownership_location_id': rec.transit_location_id.id,
            })
        
        # Create incoming mutation at destination branch
        incoming_vals = rec._prepare_incoming_mutation_vals()
        incoming_mutation = self.create(incoming_vals)
        
        # Update current record to confirmed (not done yet)
        rec.write({
            'state': 'confirmed',
            'incoming_mutation_id': incoming_mutation.id,
            'confirm_uid': self.env.user.id,
            'confirm_date': datetime.now(),
        })
        
        # Update request BPKB state if linked
        if rec.ownership_mutation_request_id:
            rec.ownership_mutation_request_id.write({
                'state': 'processed',
                'process_uid': self.env.user.id,
                'process_date': datetime.now(),
                'incoming_mutation_id': incoming_mutation.id,
            })
    
    def _confirm_incoming(self, rec):
        """Confirm incoming mutation — final step of inter-branch transfer.
        Update lot.vehicle_ownership_location_id to final destination.
        """
        for line in rec.document_mutation_line_ids:
            if rec.document_type == 'stnk':
                line.lot_id.suspend_security().write({
                    'vehicle_registration_location_id': rec.stnk_dest_location_id.id,
                })
            else:  # bpkb
                line.lot_id.suspend_security().write({
                    'vehicle_ownership_location_id': rec.bpkb_dest_location_id.id,
                })
        
        rec.write({
            'state': 'done',
            'done_uid': self.env.user.id,
            'done_date': datetime.now(),
        })
        
        # Update outgoing mutation state to done via action_done
        if rec.outgoing_mutation_id:
            rec.outgoing_mutation_id.action_done()
        
        # Update request BPKB state if linked
        if rec.ownership_mutation_request_id:
            rec.ownership_mutation_request_id.write({
                'state': 'done',
                'receipt_uid': self.env.user.id,
                'receipt_date': datetime.now(),
            })
    
    def action_done(self):
        """Mark outgoing mutation as done. Called when incoming mutation is confirmed."""
        for rec in self:
            if rec.state != 'confirmed':
                continue
            rec.write({
                'state': 'done',
                'done_uid': self.env.user.id,
                'done_date': datetime.now(),
            })

    def action_print_registration_mutation(self):
        self.ensure_one()

        return self.env.ref('tw_vehicle_document_mutation.action_print_out_registration_mutation').report_action(self)

    def action_print_ownership_mutation(self):
        self.ensure_one()

        return self.env.ref('tw_vehicle_document_mutation.action_print_out_ownership_mutation').report_action(self)
    
    def action_view_incoming(self):
        """View the related incoming mutation."""
        self.ensure_one()
        if not self.incoming_mutation_id:
            return
        action = self.env['ir.actions.act_window']._for_xml_id('tw_vehicle_document_mutation.tw_document_mutation_incoming_action')
        action['res_id'] = self.incoming_mutation_id.id
        action['views'] = [(self.env.ref('tw_vehicle_document_mutation.tw_document_mutation_incoming_view_form').id, 'form')]
        action['context'] = {'create': False, 'edit': False}
        return action
    
    def action_view_outgoing(self):
        """View the related outgoing mutation."""
        self.ensure_one()
        if not self.outgoing_mutation_id:
            return
        action = self.env['ir.actions.act_window']._for_xml_id('tw_vehicle_document_mutation.tw_document_mutation_outgoing_action')
        action['res_id'] = self.outgoing_mutation_id.id
        action['views'] = [(self.env.ref('tw_vehicle_document_mutation.tw_document_mutation_outgoing_view_form').id, 'form')]
        action['context'] = {'create': False, 'edit': False}
        return action
    
    def action_cancel(self):
        """Cancel the mutation."""
        for rec in self.filtered(lambda r: r.state in ('draft', 'confirmed')):
            rec.write({'state': 'cancel'})

    def _validate_document_mutation(self):
        for rec in self:
            if not rec.document_mutation_line_ids:
                raise UserError(_('Please add at least one document line.'))
            
            # Check for duplicate lot_ids
            lot_ids = [line.lot_id.id for line in rec.document_mutation_line_ids if line.lot_id]
            if len(lot_ids) != len(set(lot_ids)):
                raise UserError(_('Duplicate vehicle numbers are not allowed in the document lines.'))

    def _prepare_incoming_mutation_vals(self):
        """Prepare values for creating incoming mutation at destination branch.
        Uses bpkb_dest_location_id from the linked Request BPKB (filled at draft stage)
        as the final destination location at Branch B.
        """
        self.ensure_one()
        
        # Ambil lokasi tujuan akhir dari request (bukan auto-search, bukan field redundan)
        request = self.ownership_mutation_request_id
        dest_bpkb_location_id = request.bpkb_dest_location_id.id if request and request.bpkb_dest_location_id else False
        
        vals = {
            'company_id': self.destination_company_id.id,
            'document_type': self.document_type,
            'transfer_type': 'incoming',
            'source_branch_id': self.company_id.id,
            'outgoing_mutation_id': self.id,
            'ownership_mutation_request_id': request.id if request else False,
            'bpkb_source_location_id': self.transit_location_id.id if self.document_type == 'bpkb' else False,
            'bpkb_dest_location_id': dest_bpkb_location_id if self.document_type == 'bpkb' else False,
            'stnk_source_location_id': self.transit_location_id.id if self.document_type == 'stnk' else False,
            'stnk_dest_location_id': self.stnk_dest_location_id.id if self.document_type == 'stnk' and self.stnk_dest_location_id else False,
            'state': 'draft',
        }
        
        # Copy mutation lines
        mutation_lines = []
        for line in self.document_mutation_line_ids:
            mutation_lines.append((0, 0, {
                'lot_id': line.lot_id.id,
            }))
        vals['document_mutation_line_ids'] = mutation_lines
        
        return vals