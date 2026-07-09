from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('on_process', 'On Process'),
    ('processed', 'Processed'),
    ('done', 'Done'),
]


class TwVehicleOwnershipMutationRequest(models.Model):
    _name = "tw.ownership.mutation.request"
    _description = "Permohonan Mutasi BPKB"
    _order = "id desc"

    name = fields.Char(string="Name", readonly=True, default='New', copy=False)
    date = fields.Date(string='Date', default=fields.Date.today())
    process_date = fields.Datetime('Processed on')
    sending_date = fields.Datetime('Sent on')
    receipt_date = fields.Datetime('Receipt on')
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')
    # TODO : Apa itu SAP?
    sender = fields.Selection(selection=[
        ('SAP', 'SAP'),
        ('Branch', 'Dikirim Cabang')],
        string="Pengiriman")
    tracking_number = fields.Char('Tracking Number')
    courier_name = fields.Char('Courier Name')
    
    process_uid = fields.Many2one('res.users','Processed by')
    sending_uid = fields.Many2one('res.users','Sent by')
    receipt_uid = fields.Many2one('res.users', 'Receipt by')
    
    document_mutation_id = fields.Many2one('tw.document.mutation', string='Document Mutation')
    company_id = fields.Many2one('res.company', string='Branch', required=True, domain=[('parent_id', '!=', False)], default=lambda self: self.env.company)
    ownership_mutation_request_line_ids = fields.One2many('tw.ownership.mutation.request.line', 'ownership_mutation_request_id', string="Permohonan BPKB Line", copy=False)
    bpkb_source_location_id = fields.Many2one(
        'tw.vehicle.document.location',
        string='Source BPKB Location',
        domain="[('company_id', '=', company_id), ('type', '=', 'internal'), ('active', '=', True), ('document_type', '=', 'vehicle_ownership')]"
    )
    bpkb_dest_location_id = fields.Many2one(
        'tw.vehicle.document.location',
        string='Destination BPKB Location',
        check_company=False,
    )
    # Helper field untuk domain bpkb_dest_location_id di view.
    available_dest_location_ids = fields.Many2many(
        'tw.vehicle.document.location',
        relation='tw_ownership_mutation_request_avail_dest_loc_rel',
        column1='request_id',
        column2='location_id',
        string='Available Dest Locations',
        compute='_compute_available_dest_location_ids',
        store=False,
    )

    # Inter-branch mutation fields
    destination_company_id = fields.Many2one(
        'res.company',
        string='Destination Branch',
        check_company=False,
        domain="[('parent_id', '!=', False), ('id', '!=', company_id)]",
        help='Select destination branch for inter-branch mutation'
    )
    is_inter_branch = fields.Boolean(
        compute='_compute_is_inter_branch',
        store=True,
        string='Inter-Branch Mutation'
    )
    
    # Transit location — hanya untuk referensi/audit, diisi otomatis saat on_process
    transit_location_id = fields.Many2one(
        'tw.vehicle.document.location',
        string='Transit Location',
        domain="[('type', '=', 'transit'), ('active', '=', True)]",
        readonly=True,
    )
    
    # Outgoing/Incoming mutation relations
    outgoing_mutation_id = fields.Many2one(
        'tw.document.mutation',
        string='Outgoing Document'
    )
    incoming_mutation_id = fields.Many2one(
        'tw.document.mutation',
        string='Incoming Document'
    )
    outgoing_count = fields.Integer(
        compute='_compute_mutation_counts',
        string='Outgoing Count'
    )
    incoming_count = fields.Integer(
        compute='_compute_mutation_counts',
        string='Incoming Count'
    )
    
    # Domain lot for selection
    lot_ids = fields.Many2many(comodel_name='stock.lot',relation='tw_document_mutation_lot_rel',column1='document_mutation_id',column2='lot_id',compute='_compute_lot_ids',string='Serial Numbers',store=False)
    
    @api.depends('company_id', 'bpkb_source_location_id')
    def _compute_lot_ids(self):
        for record in self:
            if not record.company_id or not record.bpkb_source_location_id:
                record.lot_ids = False
                continue
                
            query = """
                SELECT sl.id 
                FROM stock_lot sl
                WHERE sl.company_id = %s
                AND sl.vehicle_ownership_receipt_id IS NOT NULL
                AND sl.ownership_handover_id IS NULL
                AND sl.vehicle_ownership_location_id = %s
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_ownership_mutation_request_line orl
                    JOIN tw_ownership_mutation_request orm ON orl.ownership_mutation_request_id = orm.id
                    WHERE orl.lot_id = sl.id 
                    AND orm.state NOT IN ('done', 'cancel')
                    AND orm.id != %s
                )
            """
            
            self._cr.execute(query, (record.company_id.id, record.bpkb_source_location_id.id, record.id or 0))
            lot_ids = [row[0] for row in self._cr.fetchall()]
            record.lot_ids = [(6, 0, lot_ids)] if lot_ids else False
            

    @api.depends('destination_company_id', 'company_id')
    def _compute_available_dest_location_ids(self):
        """Compute available destination locations dengan bypass ir.rule multi-company
        """
        Location = self.env['tw.vehicle.document.location'].sudo()
        for rec in self:
            company = rec.destination_company_id
            if company:
                rec.available_dest_location_ids = Location.search([
                    ('company_id', '=', company.id),
                    ('type', '=', 'internal'),
                    ('active', '=', True),
                    ('document_type', '=', 'vehicle_ownership'),
                ])
            else:
                rec.available_dest_location_ids = Location.browse()

    @api.depends('destination_company_id')
    def _compute_is_inter_branch(self):
        for rec in self:
            rec.is_inter_branch = bool(rec.destination_company_id)

    @api.depends('outgoing_mutation_id', 'incoming_mutation_id')
    def _compute_mutation_counts(self):
        for rec in self:
            rec.outgoing_count = 1 if rec.outgoing_mutation_id else 0
            rec.incoming_count = 1 if rec.incoming_mutation_id else 0

    # -------------------------------------------------------------------------
    # ONCHANGE
    # -------------------------------------------------------------------------

    @api.onchange('company_id')
    def onchange_company_id(self):
        for rec in self:
            rec.bpkb_source_location_id = False
            rec.bpkb_dest_location_id = False
            rec.destination_company_id = False
            rec.ownership_mutation_request_line_ids = False

    @api.onchange('bpkb_source_location_id')
    def onchange_source_location_id(self):
        for rec in self:
            rec.bpkb_dest_location_id = False
            rec.ownership_mutation_request_line_ids = False

    @api.onchange('destination_company_id')
    def onchange_destination_company_id(self):
        """Reset destination location when destination branch changes."""
        self.bpkb_dest_location_id = False

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('company_id') and values.get('name', 'New') == _('New'):
                branch_src = self.env['res.company'].suspend_security().search([
                    ('id', '=', values['company_id'])
                ], limit=1)
                values['name'] = self.env['ir.sequence'].get_sequence_code('RBP', str(branch_src.code))
        res = super().create(vals_list)
        return res

    def write(self, vals):
        res = super(TwVehicleOwnershipMutationRequest, self).write(vals)
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You cannot delete data that is not in draft status."))


    def action_on_process(self):
        """Move request to on_process state. For inter-branch, create outgoing mutation."""
        for rec in self.filtered(lambda r: r.state == 'draft'):
            rec.validate_order()
            
            if rec.is_inter_branch:
                # Create outgoing mutation for inter-branch transfer
                outgoing_mutation = rec.sudo()._create_outgoing_mutation()
                rec.write({
                    'state': 'on_process',
                    'outgoing_mutation_id': outgoing_mutation.id,
                })
            else:
                # Normal internal mutation flow
                rec.write({
                    'state': 'on_process',
                })
    
    def _create_outgoing_mutation(self):
        """Create outgoing document mutation for inter-branch transfer.
        Transit location is auto-resolved from holding company (parent of current branch).
        """
        self.ensure_one()
        
        if not self.bpkb_dest_location_id:
            raise ValidationError(_('Please select a destination BPKB location at the target branch.'))
        
        # Auto-cari transit location dari holding company (parent branch)
        holding_company = self.company_id.parent_id or self.company_id
        transit_loc = self.env['tw.vehicle.document.location'].search([
            ('company_id', '=', holding_company.id),
            ('type', '=', 'transit'),
            ('document_type', '=', 'vehicle_ownership'),
            ('active', '=', True),
        ], limit=1)
        if not transit_loc:
            raise ValidationError(
                _('Transit location not found in holding company (%s). '
                  'Please configure a transit location for BPKB document type.')
                % holding_company.name
            )
        
        # Simpan transit yang ditemukan ke record untuk audit
        self.write({'transit_location_id': transit_loc.id})
        
        mutation_vals = {
            'company_id': self.company_id.id,
            'document_type': 'bpkb',
            'transfer_type': 'outgoing',
            'destination_company_id': self.destination_company_id.id,
            'transit_location_id': transit_loc.id,
            'bpkb_source_location_id': self.bpkb_source_location_id.id,
            'bpkb_dest_location_id': transit_loc.id,
            'ownership_mutation_request_id': self.id,
            'state': 'draft',
        }
        
        # Add mutation lines from request lines
        mutation_lines = []
        for line in self.ownership_mutation_request_line_ids:
            mutation_lines.append((0, 0, {
                'lot_id': line.lot_id.id,
            }))
        
        if not mutation_lines:
            raise ValidationError(_('No valid vehicle numbers found in the request.'))
        
        mutation_vals['document_mutation_line_ids'] = mutation_lines
        return self.env['tw.document.mutation'].create(mutation_vals)

    def action_process(self):
        self.ensure_one()
        if self.state != 'on_process':
            return False
        form_id = self.env.ref('tw_vehicle_document_mutation.view_tw_ownership_mutation_request_form').id
        return {
            'name': (_('Process')),
            'res_model': 'tw.ownership.mutation.request',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form',
            'res_id': self.id,
        }

    def action_submit(self):
        for rec in self.filtered(lambda r: r.state == 'on_process'):
            rec.write({
                'state': 'processed',
                'process_uid': self.env.user.id,
                'process_date': datetime.now(),
            })
    def action_view_document_mutation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document Mutation',
            'res_model': 'tw.document.mutation',
            'view_mode': 'form',
            'res_id': self.document_mutation_id.id,
            'target': 'current',
        }
    
    def action_view_outgoing_mutation(self):
        """Smart button action to view outgoing mutation"""
        self.ensure_one()
        if not self.outgoing_mutation_id:
            return
        action = self.env['ir.actions.act_window']._for_xml_id('tw_vehicle_document_mutation.tw_document_mutation_outgoing_action')
        action['res_id'] = self.outgoing_mutation_id.id
        action['views'] = [(self.env.ref('tw_vehicle_document_mutation.tw_document_mutation_outgoing_view_form').id, 'form')]
        action['context'] = {'create': False, 'edit': False}
        return action
    
    def action_view_incoming_mutation(self):
        """Smart button action to view incoming mutation"""
        self.ensure_one()
        if not self.incoming_mutation_id:
            return
        action = self.env['ir.actions.act_window']._for_xml_id('tw_vehicle_document_mutation.tw_document_mutation_incoming_action')
        action['res_id'] = self.incoming_mutation_id.id
        action['views'] = [(self.env.ref('tw_vehicle_document_mutation.tw_document_mutation_incoming_view_form').id, 'form')]
        action['context'] = {'create': False, 'edit': False}
        return action

    def action_receive(self):
        for rec in self.filtered(lambda r: r.state == 'processed'):
            if not rec.ownership_mutation_request_line_ids:
                raise UserError(_('Please add at least one vehicle to the request.'))
                
            # Create and validate document mutation
            mutation_obj = rec._create_document_mutation()
            
            # Update the request
            rec.write({
                'state': 'done',
                'receipt_uid': self.env.user.id,
                'receipt_date': datetime.now(),
                'document_mutation_id': mutation_obj.id,
            })
            
    def action_print_ownership_mutation_request(self):
        self.ensure_one()
        return self.env.ref('tw_vehicle_document_mutation.action_print_out_ownership_mutation_request').report_action(self)
    
    def validate_order(self):
        for rec in self:
            if not rec.ownership_mutation_request_line_ids:
                raise ValidationError(_('Please input engine line.'))
                
            # Check for duplicate lots in the same request
            lot_ids = []
            for line in rec.ownership_mutation_request_line_ids:
                if line.lot_id.id in lot_ids:
                    raise ValidationError(_(f'Duplicate engine number {line.lot_id.name} found in the same request. Please remove duplicates.'))
                lot_ids.append(line.lot_id.id)
                
                # Check for existing requests with the same lot
                other_line_id = self.env['tw.ownership.mutation.request.line'].search([
                    ('lot_id', '=', line.lot_id.id),
                    ('id', '!=', line.id),
                    ('ownership_mutation_request_id.state', 'not in', ['cancel', 'done']),
                ], limit=1)
                if other_line_id:
                    raise ValidationError(_(f'Engine number {line.lot_id.name} has been requested in'
                                          f' {other_line_id.ownership_mutation_request_id.name}.'))
    def _create_document_mutation(self):
        """Create document mutation for BPKB transfer"""
        self.ensure_one()
        
        # Create document mutation with all lots
        mutation_vals = {
            'company_id': self.company_id.id,
            'document_type': 'bpkb',
            'bpkb_source_location_id': self.bpkb_source_location_id.id,
            'bpkb_dest_location_id': self.bpkb_dest_location_id.id,
            'state': 'draft',
        }
        
        # Add all lots to the mutation
        mutation_lines = []
        for line in self.ownership_mutation_request_line_ids:
            if line.lot_id:  # Ensure lot exists
                mutation_lines.append((0, 0, {
                    'lot_id': line.lot_id.id,
                }))
        
        if not mutation_lines:
            raise UserError(_('No valid vehicle numbers found in the request.'))
            
        mutation_vals['document_mutation_line_ids'] = mutation_lines
        mutation_obj = self.env['tw.document.mutation'].create(mutation_vals)
        mutation_obj.action_confirm()
        return mutation_obj