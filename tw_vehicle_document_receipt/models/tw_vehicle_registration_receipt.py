from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError as Warning

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]


class TwVehicleRegistrationReceipt(models.Model):
    _name = "tw.vehicle.registration.receipt"
    _description = "Vehicle Registration Receipt"
    _order = "name desc"

    name = fields.Char(string="Name", compute='_compute_name', store=True, default='New', copy=False)
    confirm_date = fields.Datetime('Posted on')
    cancel_date = fields.Datetime('Cancelled on')
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')
    date = fields.Date('Date', default=fields.Date.today())

    company_id = fields.Many2one('res.company', string="Branch", required=True, default=lambda self: self.env.company)
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    available_biro_jasa_ids = fields.Many2many('res.partner', compute='_compute_available_biro_jasa_ids')
    biro_jasa_id = fields.Many2one(comodel_name='res.partner', string='Biro Jasa', domain="[('id', 'in', available_biro_jasa_ids)]", required=True)
    vehicle_registration_location_id = fields.Many2one(
        comodel_name='tw.vehicle.document.location',
        string='STNK Location',
        domain="[('company_id', '=', company_id), ('type', '=', 'internal'),('active', '=', True),('document_type', '=', 'vehicle_registration')]"
    )
    vehicle_registration_receipt_line_ids = fields.One2many('tw.vehicle.registration.receipt.line', 'vehicle_registration_receipt_id', string="Vehicle Registration Receipt Line", copy=False)
    available_lot_ids = fields.Many2many('stock.lot', string='Domain Lot', compute='_compute_available_lot_ids')

    @api.depends('company_id')
    def _compute_available_biro_jasa_ids(self):
        for rec in self:
            if rec.company_id and rec.company_id.branch_setting_id:
                birojasa_settings = rec.company_id.branch_setting_id.birojasa_setting_ids
                rec.available_biro_jasa_ids = birojasa_settings.mapped('biro_jasa_id').ids
            else:
                rec.available_biro_jasa_ids = False

    @api.depends('company_id', 'biro_jasa_id')
    def _compute_available_lot_ids(self):
        for rec in self:
            if not rec.company_id or not rec.biro_jasa_id:
                rec.available_lot_ids = False
                continue
            
            # Get all lots that match the criteria
            query = """
                SELECT sl.id 
                FROM stock_lot sl
                WHERE sl.company_id = %s
                AND sl.biro_jasa_id = %s
                and sl.registration_process_id NOTNULL
                AND (
                    sl.vehicle_registration_receipt_id IS NULL 
                    OR sl.notice_receipt_id IS NULL 
                    OR sl.plate_receipt_id IS NULL
                )
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_vehicle_registration_receipt_line rpl
                    JOIN tw_vehicle_registration_receipt rp ON rpl.vehicle_registration_receipt_id = rp.id
                    WHERE rpl.lot_id = sl.id 
                    AND rp.state NOT IN ('done', 'cancel')
                    AND rpl.state != 'cancel'
                    AND rp.id != %s
                )
            """
            params = (rec.company_id.id, rec.biro_jasa_id.id, rec.id or 0)
            self._cr.execute(query, params)
            lot_ids = [row[0] for row in self._cr.fetchall()]
            
            rec.available_lot_ids = [(6, 0, lot_ids)] if lot_ids else False
            
    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if hasattr(models, 'NewId') and isinstance(rec.id, models.NewId) or not rec.id:
                    rec.name = 'New'
                    continue
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('PST', str(rec.company_id.code))

    @api.onchange('company_id','biro_jasa_id')
    def onchange_company_id(self):
        for rec in self:
            rec.vehicle_registration_receipt_line_ids = False
            rec.vehicle_registration_location_id = False

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.validate_order()
        return res

    def write(self, vals):
        res = super(TwVehicleRegistrationReceipt, self).write(vals)
        self.validate_order()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(_("You cannot delete data that is not in draft status."))

    def action_confirm(self):
        for rec in self.filtered(lambda r: r.state == 'draft'):
            rec.write({
                'state': 'done',
                'confirm_uid': self.env.user.id,
                'confirm_date': datetime.now(),
            })
            rec.vehicle_registration_receipt_line_ids.suspend_security().write(
                {'state': 'done'}
            )
            for line in rec.vehicle_registration_receipt_line_ids:
                lot_vals = {}
                if line.vehicle_registration_number and not line.vehicle_registration_received:
                    lot_vals = {
                        'vehicle_registration_receipt_id': rec.id,
                        'vehicle_registration_receipt_date': datetime.now(),
                        'vehicle_registration_location_id': rec.vehicle_registration_location_id.id,
                        'vehicle_registration_number': line.vehicle_registration_number,
                        'stnk_date': line.stnk_date,
                        'plate_number': line.plate_number,
                    }
                if line.notice_number and not line.notice_received:
                    lot_vals.update({
                        'notice_receipt_id': rec.id,
                        'notice_receipt_date': datetime.now(),
                        'notice_number': line.notice_number,
                        'notice_date': line.notice_date,
                    })
                if line.is_receive_plate and not line.plate_received:
                    lot_vals.update({
                        'plate_receipt_id': rec.id,
                        'plate_receipt_date': datetime.now(),
                    })
                line.lot_id.write(lot_vals)

    def action_cancel(self):
        for rec in self.filtered(lambda r: r.state == 'done'):
            for line in rec.vehicle_registration_receipt_line_ids:
                if line.vehicle_registration_number and line.lot_id.vehicle_registration_location_id and line.lot_id.vehicle_registration_location_id.company_id.id != rec.company_id.id:
                    raise Warning(_("Cannot cancel receipt because STNK for engine number %s has been moved to %s company on location %s.") % (line.lot_id.name, line.lot_id.vehicle_registration_location_id.company_id.name, line.lot_id.vehicle_registration_location_id.name))
                    
            rec.write({
                'state': 'cancel',
                'cancel_uid': self.env.user.id,
                'cancel_date': datetime.now(),
            })

    def action_print_out_registration_receipt(self):
        self.ensure_one()

        return self.env.ref('tw_vehicle_document_receipt.action_print_out_registration_receipt').report_action(self)

    def validate_order(self):
        for rec in self:
            if not rec.vehicle_registration_receipt_line_ids:
                raise Warning(_('Please input engine line.'))
                
            # Check for duplicate lots in the same receipt
            lot_ids = []
            for line in rec.vehicle_registration_receipt_line_ids:
                if line.lot_id.id in lot_ids:
                    raise Warning(_('Duplicate engine number %s found in the same receipt.') % line.lot_id.name)
                lot_ids.append(line.lot_id.id)
                lot = line.lot_id
                
                # Check if this lot is already processed in another receipt
                existing_receipts = self.env['tw.vehicle.registration.receipt'].search([
                    ('id', '!=', rec.id),
                    ('state', '!=', 'cancel'),
                    ('vehicle_registration_receipt_line_ids.lot_id', '=', lot.id),
                ])
                
                # Check for conflicts with existing receipts
                for receipt in existing_receipts:
                    existing_line = receipt.vehicle_registration_receipt_line_ids.filtered(
                        lambda l: l.lot_id == lot
                    )
                    
                    # Only prevent if the same document type is being processed again
                    if existing_line:
                        conflict_fields = []
                        # Only check for conflicts if we're trying to receive the same document type
                        if (line.vehicle_registration_number and not line.vehicle_registration_received and 
                            lot.vehicle_registration_receipt_id and 
                            lot.vehicle_registration_receipt_id.id != rec.id):
                            conflict_fields.append('STNK')
                            
                        if (line.is_receive_plate and not line.plate_received and 
                            lot.plate_receipt_id and 
                            lot.plate_receipt_id.id != rec.id):
                            conflict_fields.append('Plat')
                            
                        if (line.notice_number and not line.notice_received and 
                            lot.notice_receipt_id and 
                            lot.notice_receipt_id.id != rec.id):
                            conflict_fields.append('Notice')
                            
                        if conflict_fields:
                            raise Warning(
                                _('Engine number %s has already been processed for %s in %s.') % 
                                (lot.name, ', '.join(conflict_fields), receipt.name)
                            )
                # Gunakan state lot dari DATABASE sebagai sumber kebenaran
                # agar konsisten dan tidak terpengaruh oleh onchange pre-fill
                missing_docs = []
                if not line.notice_number and not line.lot_id.notice_receipt_id:
                    missing_docs.append('Notice')
                if not line.vehicle_registration_number and not line.lot_id.vehicle_registration_receipt_id:
                    missing_docs.append('STNK')
                if not line.plate_number and not line.lot_id.vehicle_registration_receipt_id:
                    missing_docs.append('Nomor Plat')
                if not line.is_receive_plate and not line.lot_id.plate_receipt_id:
                    missing_docs.append('Terima Plat')

                receiving_now = sum([
                    bool(line.notice_number and not line.lot_id.notice_receipt_id),
                    bool(line.vehicle_registration_number and not line.lot_id.vehicle_registration_receipt_id),
                    bool(line.is_receive_plate and not line.lot_id.plate_receipt_id),
                ])

                # Warning hanya jika tidak ada satupun yang sedang diterima dalam transaksi ini
                if receiving_now == 0:
                    raise Warning(
                        _('Please specify at least one item to receive for engine %s\n\n'
                        'Documents not yet received:\n'
                        '- %s') % (lot.name, '\n- '.join(missing_docs))
                    )
