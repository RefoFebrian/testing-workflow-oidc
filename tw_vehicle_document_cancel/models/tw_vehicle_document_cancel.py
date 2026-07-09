# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwVehicleDocumentCancel(models.Model):
    _name = "tw.vehicle.document.cancel"
    _description = 'Penerimaan/Penyerahan Faktur Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ["mail.thread", "tw.approval.mixin"]
    _order = 'id desc'

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string="Name", compute='_compute_name', store=True, default='New', copy=False)
    # 9: relation fields
    vehicle_document_request_id = fields.Many2one(
        'tw.vehicle.document.request', 
        'Permohonan Faktur',
    )
    vehicle_document_receive_id = fields.Many2one(
        'tw.vehicle.document.receive', 
        'Penerimaan Faktur',
    )
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')
    vehicle_document_cancel_line_ids = fields.One2many('tw.vehicle.document.cancel.line', 'cancel_id', 'Cancel Line')
    available_lot_ids = fields.Many2many('stock.lot', string='Domain Lot', compute='_compute_available_lot_ids')
    available_request_ids = fields.Many2many(
        'tw.vehicle.document.request',
        string='Available Requests',
        compute='_compute_available_request_receive_ids'
    )
    available_receive_ids = fields.Many2many(
        'tw.vehicle.document.receive',
        string='Available Receives',
        compute='_compute_available_request_receive_ids'
    )

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_available_request_receive_ids(self):
        """Compute available request and receive documents that have cancellable lots."""
        for record in self:
            available_requests = []
            available_receives = []
            
            if record.company_id:
                # Query for requests with cancellable lots
                self._cr.execute("""
                    SELECT DISTINCT r.id
                    FROM tw_vehicle_document_request r
                    INNER JOIN tw_vehicle_document_request_line rl ON rl.vehicle_document_request_id = r.id
                    INNER JOIN stock_lot sl ON sl.id = rl.lot_id
                    WHERE r.company_id = %s
                    AND r.state = 'done'
                    AND rl.state != 'cancel'
                    AND sl.vehicle_document_receive_id IS NULL
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tw_vehicle_document_cancel_line cl
                        JOIN tw_vehicle_document_cancel c ON cl.cancel_id = c.id
                        LEFT JOIN tw_cancellation tc ON c.cancellation_id = tc.id
                        WHERE cl.lot_id = sl.id 
                        AND tc.state != 'confirmed'
                        AND c.id != %s
                    )
                """, (record.company_id.id, record.id or 0))
                available_requests = [row[0] for row in self._cr.fetchall()]
                
                # Query for receives with cancellable lots
                self._cr.execute("""
                    SELECT DISTINCT r.id
                    FROM tw_vehicle_document_receive r
                    INNER JOIN tw_vehicle_document_receive_line rl ON rl.vehicle_document_receive_id = r.id
                    INNER JOIN stock_lot sl ON sl.id = rl.lot_id
                    WHERE r.company_id = %s
                    AND r.state = 'done'
                    AND rl.state != 'cancel'
                    AND sl.registration_process_id IS NULL
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tw_vehicle_document_cancel_line cl
                        JOIN tw_vehicle_document_cancel c ON cl.cancel_id = c.id
                        LEFT JOIN tw_cancellation tc ON c.cancellation_id = tc.id
                        WHERE cl.lot_id = sl.id 
                        AND tc.state != 'confirmed'
                        AND c.id != %s
                    )
                """, (record.company_id.id, record.id or 0))
                available_receives = [row[0] for row in self._cr.fetchall()]
            
            record.available_request_ids = [(6, 0, available_requests)]
            record.available_receive_ids = [(6, 0, available_receives)]
    
    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if hasattr(models, 'NewId') and isinstance(rec.id, models.NewId) or not rec.id:
                    rec.name = 'New'
                    continue
                code = 'CPF'
                if rec.vehicle_document_receive_id:
                    code = 'CPNF'
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code(code, str(rec.company_id.code))
    
    @api.depends('vehicle_document_request_id', 'vehicle_document_receive_id')
    def _compute_available_lot_ids(self):
        for record in self:
            record.available_lot_ids = False
            
            if record.vehicle_document_request_id:
                # Search for lots that have this request_id and null receive_id
                # and not used in other active cancellations
                query = """
                    SELECT sl.id 
                    FROM stock_lot sl
                    LEFT JOIN tw_vehicle_document_request_line rl ON rl.vehicle_document_request_id = sl.vehicle_document_request_id
                    WHERE sl.vehicle_document_request_id = %s
                    AND sl.vehicle_document_receive_id IS NULL
                    AND sl.id IN %s
                    AND rl.state !='cancel'
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tw_vehicle_document_cancel_line cl
                        JOIN tw_vehicle_document_cancel c ON cl.cancel_id = c.id
                        LEFT JOIN tw_cancellation tc ON c.cancellation_id = tc.id
                        WHERE cl.lot_id = sl.id 
                        AND tc.state != 'confirmed'
                        AND c.id != %s
                    )
                """
                lot_ids = tuple(record.vehicle_document_request_id.vehicle_document_request_line_ids.mapped('lot_id').ids)
                if lot_ids:
                    params = (record.vehicle_document_request_id.id, lot_ids, record.id or 0)
                    self._cr.execute(query, params)
                    valid_lot_ids = [row[0] for row in self._cr.fetchall()]
                    record.available_lot_ids = [(6, 0, valid_lot_ids)] if valid_lot_ids else False
                    
            elif record.vehicle_document_receive_id:
                # Search for lots that have this receive_id and null registration_process_id
                # and not used in other active cancellations
                query = """
                    SELECT sl.id 
                    FROM stock_lot sl
                    LEFT JOIN tw_vehicle_document_receive_line rl ON rl.vehicle_document_receive_id = sl.vehicle_document_receive_id
                    WHERE sl.vehicle_document_receive_id = %s
                    AND sl.registration_process_id IS NULL
                    AND sl.id IN %s
                    AND rl.state !='cancel'
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tw_vehicle_document_cancel_line cl
                        JOIN tw_vehicle_document_cancel c ON cl.cancel_id = c.id
                        LEFT JOIN tw_cancellation tc ON c.cancellation_id = tc.id
                        WHERE cl.lot_id = sl.id 
                        AND tc.state != 'confirmed'
                        AND c.id != %s
                    )
                """
                lot_ids = tuple(record.vehicle_document_receive_id.vehicle_document_receive_line_ids.mapped('lot_id').ids)
                if lot_ids:
                    params = (record.vehicle_document_receive_id.id, lot_ids, record.id or 0)
                    self._cr.execute(query, params)
                    valid_lot_ids = [row[0] for row in self._cr.fetchall()]
                    record.available_lot_ids = [(6, 0, valid_lot_ids)] if valid_lot_ids else False

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.vehicle_document_request_id = False
        self.vehicle_document_receive_id = False

    @api.onchange('vehicle_document_request_id','vehicle_document_receive_id')
    def _onchange_vehicle_document_request_id(self):
        self.transaction_name = False
        self.vehicle_document_cancel_line_ids = False
        if self.vehicle_document_request_id:
            self.transaction_name = self.vehicle_document_request_id.name
        if self.vehicle_document_receive_id:
            self.transaction_name = self.vehicle_document_receive_id.name
                
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            vals['date'] = self._get_default_date()
        return super(TwVehicleDocumentCancel, self).create(vals_list)


    def action_confirm(self):
        self._validity_check()
        for line in self.vehicle_document_cancel_line_ids:
            vals = {}
            # Handle request cancellation
            if self.vehicle_document_request_id:
                # Cancel request lines for this lot
                request_lines = self.vehicle_document_request_id.vehicle_document_request_line_ids.filtered(
                    lambda l: l.lot_id == line.lot_id and l.state != 'cancel'
                )
                if request_lines:
                    request_lines.action_cancel()
                    
                vals.update({
                    'vehicle_document_request_id': False,
                    'vehicle_document_request_date': False,
                    'document_state': False
                })
                
            # Handle receive cancellation
            if self.vehicle_document_receive_id:
                # Cancel receive lines for this lot
                receive_lines = self.vehicle_document_receive_id.vehicle_document_receive_line_ids.filtered(
                    lambda l: l.lot_id == line.lot_id and l.state != 'cancel'
                )
                if receive_lines:
                    receive_lines.action_cancel()
                vals.update({
                    'vehicle_document_receive_id': False,
                    'vehicle_document_receive_date': False,
                    'document_state': 'document_request',
                    'print_date': False,
                    'doc_number': False,
                })
                
            # Update lot information
            if vals:
                line.lot_id.suspend_security().write(vals)
                
        # Cancel the document if all lines are cancelled
        if self.vehicle_document_request_id:
            request_lines = self.vehicle_document_request_id.vehicle_document_request_line_ids
            if request_lines and all(line.state == 'cancel' for line in request_lines):
                self.vehicle_document_request_id.action_cancel()
        
        if self.vehicle_document_receive_id:
            receive_lines = self.vehicle_document_receive_id.vehicle_document_receive_line_ids
            if receive_lines and all(line.state == 'cancel' for line in receive_lines):
                self.vehicle_document_receive_id.action_cancel()
            
        return self.cancellation_id.action_confirm()

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You cannot delete data that is not in draft status."))

    def _validity_check(self):
        """Validate document cancellation with optimized checks."""
        for rec in self:
            if not rec.vehicle_document_request_id and not rec.vehicle_document_receive_id:
                continue

            # Early exit if no lines
            if not rec.vehicle_document_cancel_line_ids:
                raise ValidationError(_('Please add at least one lot to cancel.'))

            # Get all lots and check for duplicates
            cancel_lots = rec.vehicle_document_cancel_line_ids.mapped('lot_id')
            if len(cancel_lots) != len(set(cancel_lots)):
                dupes = [lot.name for lot in cancel_lots 
                        if cancel_lots.filtered(lambda l: l == lot).mapped('id').count(lot.id) > 1]
                raise ValidationError(_(
                    f'Duplicate lots found: {", ".join(set(dupes))}. '
                    'Please remove duplicates.'
                ))

            if rec.vehicle_document_request_id:
                # Validate request cancellation
                if rec.vehicle_document_request_id.state == 'cancel':
                    raise ValidationError(_(
                        f'Document request {rec.vehicle_document_request_id.name} is already cancelled.'
                    ))

                # Get valid lots for request cancellation
                valid_lots = self.env['stock.lot'].search([
                    ('id', 'in', rec.vehicle_document_request_id.vehicle_document_request_line_ids.lot_id.ids),
                    ('vehicle_document_receive_id', '=', False)
                ])

                # Check lot validity
                invalid_lots = rec.vehicle_document_cancel_line_ids.filtered(
                    lambda l: l.lot_id not in valid_lots
                )

            elif rec.vehicle_document_receive_id:
                # Validate receive cancellation
                if rec.vehicle_document_receive_id.state == 'cancel':
                    raise ValidationError(_(
                        f'Document receive {rec.vehicle_document_receive_id.name} is already cancelled.'
                    ))

                # Get valid lots for receive cancellation
                valid_lots = self.env['stock.lot'].search([
                    ('id', 'in', rec.vehicle_document_receive_id.vehicle_document_receive_line_ids.lot_id.ids),
                    ('registration_process_id', '=', False)
                ])

                # Check lot validity
                invalid_lots = rec.vehicle_document_cancel_line_ids.filtered(
                    lambda l: l.lot_id not in valid_lots
                )

            # Check active cancellations in batch
            lot_ids = tuple(cancel_lots.ids)
            if lot_ids:
                self._cr.execute("""
                    SELECT cl.lot_id 
                    FROM tw_vehicle_document_cancel_line cl
                    JOIN tw_vehicle_document_cancel c ON cl.cancel_id = c.id
                    LEFT JOIN tw_cancellation tc ON c.cancellation_id = tc.id
                    WHERE cl.lot_id IN %s 
                    AND tc.state != 'confirmed'
                    AND c.id != %s
                """, (lot_ids, rec.id or 0))
                
                active_lot_ids = {row[0] for row in self._cr.fetchall()}
                invalid_lots |= rec.vehicle_document_cancel_line_ids.filtered(
                    lambda l: l.lot_id.id in active_lot_ids
                )

            # Raise error if any invalid lots
            if invalid_lots:
                raise ValidationError((
                    'The following lots cannot be cancelled:\n' +
                    '\n'.join([
                        f"- {lot.name}: {'Not in document' if lot not in valid_lots else 'Already processed' if (rec.vehicle_document_request_id and lot.vehicle_document_receive_id) or (rec.vehicle_document_receive_id and lot.registration_process_id) else 'In another cancellation'}" 
                        for lot in invalid_lots.mapped('lot_id')
                    ])
                ))

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)

    def action_request_approval(self):
        return super().action_request_approval(value=5)
    
    def validate_order(self):
        self.ensure_one()
        self._validity_check()
        return super().validate_order()
        
        