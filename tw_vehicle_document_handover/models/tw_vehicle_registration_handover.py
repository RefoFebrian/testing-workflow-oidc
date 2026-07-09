from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]


class TwVehicleGiveStnk(models.Model):
    _name = "tw.vehicle.registration.handover"
    _description = "Penyerahan STNK"
    _order = "id desc"

    name = fields.Char(string="Name", readonly=True, default='New', copy=False, index=True, compute='_compute_name', store=True)
    receiver = fields.Char(string='Penerima',required=True)
    note = fields.Text(string="Notes",required=False)
    confirm_date = fields.Datetime('Posted on')
    cancel_date = fields.Datetime('Cancelled on')
    date = fields.Date(string='Date', default=fields.Date.today())
    
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')
    
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    company_id = fields.Many2one('res.company', string='Branch', required=True, domain=[('parent_id', '!=', False)], default=lambda self: self.env.company)
    partner_id = fields.Many2one(comodel_name='res.partner',string='Customer',required=False)
    registration_handover_line_ids = fields.One2many('tw.vehicle.registration.handover.line', 'vehicle_registration_handover_id', string="Penyerahan STNK Line", copy=True)
    available_lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        string='Domain Lot',
        compute='_compute_available_lot_ids',
    )
    
    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if hasattr(models, 'NewId') and isinstance(rec.id, models.NewId) or not rec.id:
                    rec.name = 'New'
                    continue
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('ENCS', str(rec.company_id.code))

    @api.depends('company_id', 'partner_id')
    def _compute_available_lot_ids(self):
        for rec in self:
            if not rec.company_id:
                rec.available_lot_ids = False
                continue
            where = ""
            if rec.partner_id:
                where = " AND sl.customer_stnk_id = %s" % rec.partner_id.id
            # Base query without customer filter
            query = f"""
                SELECT sl.id 
                FROM stock_lot sl
                LEFT JOIN tw_stock_document tsd on tsd.lot_id = sl.id and tsd.type = 'stnk'
                WHERE tsd.company_id = {rec.company_id.id}
                {where}
                AND sl.vehicle_registration_receipt_id NOTNULL
                AND sl.notice_receipt_id NOTNULL
                AND sl.birojasa_billing_date NOTNULL
                AND (
                    sl.registration_handover_id IS NULL
                    OR sl.notice_handover_id IS NULL
                    OR sl.plate_handover_id IS NULL
                )
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_vehicle_registration_handover_line rpl
                    JOIN tw_vehicle_registration_handover rp 
                        ON rpl.vehicle_registration_handover_id = rp.id
                    WHERE rpl.lot_id = sl.id 
                    AND rp.state NOT IN ('done', 'cancel')
                    AND rpl.state != 'cancel'
                    AND rp.id != {rec.id or 0}
                )
            """
            self._cr.execute(query)
            lot_ids = [row[0] for row in self._cr.fetchall()]
            
            rec.available_lot_ids = [(6, 0, lot_ids)] if lot_ids else False
    
    @api.onchange('company_id')
    def onchange_company_id(self):
        for rec in self:
            rec.registration_handover_line_ids = False
            rec.partner_id = False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.receiver = False
        self.registration_handover_line_ids = False
        for rec in self:
            if rec.partner_id:
                rec.receiver = rec.partner_id.name

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.validate_order()
        return records
    
    def write(self, vals):
        res = super(TwVehicleGiveStnk, self).write(vals)
        self.validate_order()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You cannot delete data that is not in draft status."))


    def action_confirm(self):
        for rec in self.filtered(lambda r: r.state == 'draft'):
            rec.suspend_security().write({
                'state': 'done',
                'confirm_uid': self.env.user.id,
                'confirm_date': datetime.now(),
            })
            rec.registration_handover_line_ids.suspend_security().write({
                'state': 'done',
            })
            for line in rec.registration_handover_line_ids:
                vals = {}
                if line.stnk_handover_date and not line.lot_id.registration_handover_id:
                    vals['registration_handover_date'] = line.stnk_handover_date
                    vals['registration_handover_id'] = rec.id
                    vals['registration_receiver'] = rec.receiver
                if line.notice_handover_date and not line.lot_id.notice_handover_id:
                    vals['notice_handover_date'] = line.notice_handover_date
                    vals['notice_handover_id'] = rec.id
                    vals['notice_receiver'] = rec.receiver
                if line.plate_handover_date and not line.lot_id.plate_handover_id:
                    vals['plate_handover_date'] = line.plate_handover_date
                    vals['plate_handover_id'] = rec.id
                    vals['plate_receiver'] = rec.receiver
                if vals:
                    line.lot_id.suspend_security().write(vals)

    def action_cancel(self):
        for rec in self.filtered(lambda r: r.state == 'done'):
            rec.suspend_security().write({
                'state': 'cancel',
                'cancel_uid': self.env.user.id,
                'cancel_date': datetime.now(),
            })
            rec.registration_handover_line_ids.action_cancel()

    def action_print_out_registration_handover(self):
        self.ensure_one()

        return self.env.ref('tw_vehicle_document_handover.action_print_out_registration_handover').report_action(self)
                

    def validate_order(self):
        for rec in self:
            if not rec.registration_handover_line_ids:
                raise ValidationError(_('Please input engine line.'))
                
            # Check for duplicate lots in the same handover
            lot_ids = []
            for line in rec.registration_handover_line_ids:
                if line.lot_id.id in lot_ids:
                    raise ValidationError(_('Duplicate engine number %s found in the same handover.') % line.lot_id.name)
                
                if not line.lot_id.vehicle_registration_receipt_id:
                    raise ValidationError(_('Engine number %s has not been BPKB received') % line.lot_id.name)
                if not line.lot_id.notice_receipt_id:
                    raise ValidationError(_('Engine number %s has not been Notice received') % line.lot_id.name)
                if not line.lot_id.plate_receipt_id and line.plate_handover_date:
                    raise ValidationError(_('Engine number %s has not been Plate received') % line.lot_id.name)
                if not line.lot_id.birojasa_billing_date:
                    raise ValidationError(_('Engine number %s has not been Birojasa billing') % line.lot_id.name)
                
                if line.lot_id.vehicle_registration_location_id.company_id.id != rec.company_id.id:
                    raise ValidationError(_('Engine number %s has not been at the same location') % line.lot_id.name)
                
                lot_ids.append(line.lot_id.id)
                lot = line.lot_id
                
                # Check if this lot is already being processed in another handover
                existing_handovers = self.env['tw.vehicle.registration.handover'].search([
                    ('id', '!=', rec.id),
                    ('state', '!=', 'cancel'),
                    ('registration_handover_line_ids.lot_id', '=', lot.id),
                    ('state', '!=', 'cancel')
                ])
                
                # Check for conflicts with existing handovers
                for handover in existing_handovers:
                    existing_line = handover.registration_handover_line_ids.filtered(
                        lambda l: l.lot_id == lot
                    )
                    
                    if existing_line and handover.state not in ['cancel', 'done']:
                        conflict_fields = []
                        # Check for each document type being handed over
                        if (line.stnk_handover_date and 
                            lot.registration_handover_id and 
                            lot.registration_handover_id.id != rec.id):
                            conflict_fields.append('STNK')
                            
                        if (line.notice_handover_date and 
                            lot.notice_handover_id and 
                            lot.notice_handover_id.id != rec.id):
                            conflict_fields.append('Notice')
                            
                        if (line.plate_handover_date and 
                            lot.plate_handover_id and 
                            lot.plate_handover_id.id != rec.id):
                            conflict_fields.append('Plat')
                            
                        if conflict_fields:
                            raise ValidationError(
                                _('Engine number %s has already been processed for %s in %s.') % 
                                (lot.name, ', '.join(conflict_fields), handover.name)
                            )
                
                # Check which documents are being handed over in this transaction
                unchecked_count = sum([
                    not line.notice_handover, 
                    not line.plate_handover, 
                    not line.vehicle_registration_handover, 
                ])

                # Check which documents are still available for handover
                available_docs = []
                if not line.notice_handover_date and not line.notice_handover:
                    available_docs.append('Notice')
                if not line.plate_handover_date and not line.plate_handover:
                    available_docs.append('Plate')
                if not line.stnk_handover_date and not line.vehicle_registration_handover:
                    available_docs.append('STNK')

                if unchecked_count == len(available_docs):
                    raise ValidationError(
                        _('Please specify at least one item to hand over for engine %s\n\n' 
                        'Available documents for handover:\n' 
                        '- %s') % (lot.name, '\n- '.join(available_docs))
                    )