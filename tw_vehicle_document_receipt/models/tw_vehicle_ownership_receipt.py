from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]


class TwVehicleOwnershipReceipt(models.Model):
    _name = "tw.vehicle.ownership.receipt"
    _description = "Vehicle Ownership Receipt"
    _order = "id desc"

    name = fields.Char(string="Name", compute='_compute_name', store=True, default='New', copy=False)
    confirm_date = fields.Datetime('Posted on')
    cancel_date = fields.Datetime('Cancelled on')
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')
    date = fields.Date('Date', default=fields.Date.today())
    is_for_other_branch = fields.Boolean(string='Terima atas Branch Lain?', default=False)

    company_id = fields.Many2one('res.company', string="Branch", required=True, default=lambda self: self.env.company)
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    vehicle_ownership_location_id = fields.Many2one(comodel_name='tw.vehicle.document.location', string='BPKB Location', domain="[('company_id', '=', company_id), ('type', '=', 'internal'), ('active', '=', True),('document_type', '=', 'vehicle_ownership')]")
    available_biro_jasa_ids = fields.Many2many('res.partner', compute='_compute_available_biro_jasa_ids')
    biro_jasa_id = fields.Many2one(comodel_name='res.partner', string='Biro Jasa', domain="[('id', 'in', available_biro_jasa_ids)]", required=True)
    dest_company_id = fields.Many2one(
        'res.company', string='Branch Tujuan',
        check_company=False,
        domain="[('parent_id', '!=', False), ('id', '!=', company_id)]"
    )
    dest_ownership_location_id = fields.Many2one(
        comodel_name='tw.vehicle.document.location',
        string='Lokasi BPKB Tujuan',
        check_company=False,
        domain="[('company_id', '=', dest_company_id), ('type', '=', 'internal'), ('active', '=', True), ('document_type', '=', 'vehicle_ownership')]"
    )
    vehicle_ownership_receipt_line_ids = fields.One2many('tw.vehicle.ownership.receipt.line', 'vehicle_ownership_receipt_id', string="BPKB Receive Line", copy=False)
    available_lot_ids = fields.Many2many('stock.lot', string='Domain Lot', compute='_compute_available_lot_ids')

    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if hasattr(models, 'NewId') and isinstance(rec.id, models.NewId) or not rec.id:
                    rec.name = 'New'
                    continue
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('PSB', str(rec.company_id.code))

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
                AND sl.registration_process_id  NOTNULL
                AND sl.vehicle_ownership_receipt_id IS NULL
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_vehicle_ownership_receipt_line rpl
                    JOIN tw_vehicle_ownership_receipt rp ON rpl.vehicle_ownership_receipt_id = rp.id
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

    @api.onchange('company_id', 'biro_jasa_id')
    def onchange_company_id(self):
        for rec in self:
            rec.vehicle_ownership_receipt_line_ids = False
            rec.vehicle_ownership_location_id = False
            rec.is_for_other_branch = False
            rec.dest_company_id = False
            rec.dest_ownership_location_id = False

    @api.onchange('is_for_other_branch')
    def _onchange_is_for_other_branch(self):
        if not self.is_for_other_branch:
            self.dest_company_id = False
            self.dest_ownership_location_id = False

    @api.onchange('dest_company_id')
    def _onchange_dest_company_id(self):
        self.dest_ownership_location_id = False

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.validate_order()
        return res

    def write(self, vals):
        res = super(TwVehicleOwnershipReceipt, self).write(vals)
        self.validate_order()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You cannot delete data that is not in draft status."))

    def action_confirm(self):
        for rec in self.filtered(lambda r: r.state == 'draft'):
            rec.write({
                'state': 'done',
                'confirm_uid': self.env.user.id,
                'confirm_date': datetime.now(),
            })
            rec.vehicle_ownership_receipt_line_ids.suspend_security().write(
                {'state': 'done'}
            )

            for line in rec.vehicle_ownership_receipt_line_ids:
                # Tentukan branch dan lokasi final berdasarkan apakah penerimaan atas branch lain
                target_company_id = rec.dest_company_id.id if rec.is_for_other_branch and rec.dest_company_id else rec.company_id.id
                target_location_id = rec.dest_ownership_location_id.id if rec.is_for_other_branch and rec.dest_ownership_location_id else rec.vehicle_ownership_location_id.id

                line.lot_id.write({
                    'vehicle_ownership_receipt_id': rec.id,
                    'vehicle_ownership_receipt_date': rec.date,
                    'vehicle_ownership_location_id': target_location_id,
                    'vehicle_ownership_number': line.vehicle_ownership_number,
                    'vehicle_ownership_order_number': line.vehicle_ownership_order_number,
                    'vehicle_ownership_date': line.vehicle_ownership_date,
                })

    def action_cancel(self):
        for rec in self.filtered(lambda r: r.state == 'done'):
            target_location_id = rec.dest_ownership_location_id.id if rec.is_for_other_branch and rec.dest_ownership_location_id else rec.vehicle_ownership_location_id.id
            for line in rec.vehicle_ownership_receipt_line_ids:
                if line.vehicle_ownership_number and line.lot_id.vehicle_ownership_location_id and line.lot_id.vehicle_ownership_location_id.id != target_location_id:
                    raise ValidationError(_("Cannot cancel receipt because BPKB for engine number %s has been moved to %s.") % (line.lot_id.name, line.lot_id.vehicle_ownership_location_id.name))
                    
            rec.write({
                'state': 'cancel',
                'cancel_uid': self.env.user.id,
                'cancel_date': datetime.now(),
            })

    def action_print_out_ownership_receipt(self):
        self.ensure_one()

        return self.env.ref('tw_vehicle_document_receipt.action_print_out_ownership_receipt').report_action(self)

    def validate_order(self):
        for rec in self:
            if not rec.vehicle_ownership_receipt_line_ids:
                raise ValidationError(_('Please input engine line.'))
                
            # Check for duplicate lots in the same receipt
            lot_ids = set()
            duplicate_lots = set()
            
            # Check for duplicates in other receipts
            for line in rec.vehicle_ownership_receipt_line_ids:
                if line.lot_id.id in lot_ids:
                    duplicate_lots.add(line.lot_id.name)
                lot_ids.add(line.lot_id.id)

                other_line_id = self.env['tw.vehicle.ownership.receipt.line'].search([
                    ('lot_id', '=', line.lot_id.id),
                    ('vehicle_ownership_receipt_id', '!=', line.vehicle_ownership_receipt_id.id),
                    ('vehicle_ownership_receipt_id.state', '!=', 'cancel'),
                    ('state', '!=', 'cancel'),
                ], limit=1)
                if other_line_id:
                    raise ValidationError(_('Engine number %s has been processed in %s') % 
                                    (line.lot_id.name, other_line_id.vehicle_ownership_receipt_id.name))
            if duplicate_lots:
                raise ValidationError(_('Duplicate engine numbers in the same receipt: %s') % 
                                    ', '.join(sorted(duplicate_lots)))
            