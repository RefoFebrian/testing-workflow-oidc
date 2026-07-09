from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]


class TwVehicleOwnershipHandover(models.Model):
    _name = "tw.vehicle.ownership.handover"
    _description = "Penyerahan BPKB"
    _order = "id desc"

    name = fields.Char(string="Name", readonly=True, default='New', copy=False, index=True, compute='_compute_name', store=True)
    confirm_date = fields.Datetime('Posted on')
    cancel_date = fields.Datetime('Cancelled on')
    date = fields.Date(string='Date', default=fields.Date.today())
    receiver = fields.Char(string='Penerima', required=True)
    note = fields.Text(string="Notes", required=False)
    ownership_handover_date = fields.Date(string='Tgl Penyerahan BPKB', required=False)
    count_printed = fields.Integer(string='Print Ke', default=0)
    
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    print_count = fields.Integer(string="Print Count", default=0, copy=False)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')
    partner_type = fields.Selection(string='Partner Type', selection=[
            ('customer', 'Customer'),
            ('finco', 'Finance Company'),
        ], required=True)
    
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    
    company_id = fields.Many2one('res.company', string='Branch', required=True, domain=[('parent_id', '!=', False)], default=lambda self: self.env.company)
    partner_id = fields.Many2one(comodel_name='res.partner', string='A/N BPKB', required=False)
    ownership_handover_line_ids = fields.One2many('tw.vehicle.ownership.handover.line', 'ownership_handover_id', string="Penyerahan BPKB Line", copy=True)
    allowed_partner_ids = fields.Many2many(comodel_name='res.partner',compute='_compute_allowed_partners',string='Allowed Partners')
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
                    rec.name = self.env['ir.sequence'].get_sequence_code('ENCB', str(rec.company_id.code))

    @api.depends('partner_type')
    def _compute_allowed_partners(self):
        for rec in self:
            partner_obj = self.env['res.partner']
            if self.partner_type == 'customer':
                partner_domain = [
                    ('category_id.name', 'in', ['Customer'])
                ]
            else:
                partner_domain = [
                    ('category_id.name', '=', 'Finance Company')
                ]
            allowed_partner_ids = partner_obj.suspend_security().search(partner_domain)
            rec.allowed_partner_ids = allowed_partner_ids

    @api.depends('company_id', 'partner_id')
    def _compute_available_lot_ids(self):
        for rec in self:
            if not rec.company_id:
                rec.available_lot_ids = False
                continue
                
            where = ""
            if rec.partner_id:
                if rec.partner_type == 'customer':
                    where = " AND sl.customer_stnk_id = %d" % rec.partner_id.id
                else:
                    where = " AND sl.finco_id = %d" % rec.partner_id.id
                    
            # Base query with ownership and billing filters
            query = f"""
                SELECT sl.id 
                FROM stock_lot sl
                LEFT JOIN tw_stock_document tsd on tsd.lot_id = sl.id and tsd.type = 'bpkb'
                WHERE tsd.company_id = {rec.company_id.id}
                {where}
                AND sl.vehicle_ownership_receipt_id IS NOT NULL
                AND sl.vehicle_ownership_receipt_id != 0
                AND sl.birojasa_billing_date IS NOT NULL
                AND sl.ownership_handover_id IS NULL
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_vehicle_ownership_handover_line opl
                    JOIN tw_vehicle_ownership_handover op 
                        ON opl.ownership_handover_id = op.id
                    WHERE opl.lot_id = sl.id 
                    AND op.state NOT IN ('done', 'cancel')
                    AND opl.state != 'cancel'
                    AND op.id != {rec.id or 0}
                )
            """
            self._cr.execute(query)
            lot_ids = [row[0] for row in self._cr.fetchall()]
            
            rec.available_lot_ids = [(6, 0, lot_ids)] if lot_ids else False


    @api.onchange('partner_type')
    def onchange_partner_type(self):
        self.receiver = False
        self.partner_id = False 
        self.ownership_handover_line_ids = False
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.receiver = False
        self.ownership_handover_line_ids = False
        for rec in self:
            if rec.partner_id:
                rec.receiver = rec.partner_id.name

    @api.onchange('company_id')
    def onchange_company_id(self):
        for rec in self:
            rec.ownership_handover_line_ids = False
            rec.partner_type = False
    
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.validate_order()
        return records

    def write(self, vals):
        res = super(TwVehicleOwnershipHandover, self).write(vals)
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
            rec.ownership_handover_line_ids.suspend_security().write({
                'state': 'done',
            })
            for line in rec.ownership_handover_line_ids:
                line.lot_id.suspend_security().write({
                    'ownership_handover_id': rec.id,
                    'ownership_handover_date': line.ownership_handover_date,
                    'ownership_receiver': rec.receiver,
                })

    def action_cancel(self):
        for rec in self.filtered(lambda r: r.state == 'done'):
            rec.suspend_security().write({
                'state': 'cancel',
                'cancel_uid': self.env.user.id,
                'cancel_date': datetime.now(),
            })

    def action_print_out_ownership_handover_customer(self):
        self.ensure_one()
        self.count_printed += 1
        return self.env.ref('tw_vehicle_document_handover.action_print_out_ownership_handover_customer').report_action(self)

    def action_print_out_ownership_handover_company(self):
        self.ensure_one()
        self.count_printed += 1
        return self.env.ref('tw_vehicle_document_handover.action_print_out_ownership_handover_company').report_action(self)
    
    def validate_order(self):
        for rec in self:
            if not rec.ownership_handover_line_ids:
                raise ValidationError(_('Please input engine line.'))
                
            # Check for duplicate lots within the same transaction
            lot_ids = []
            for line in rec.ownership_handover_line_ids:
                if not line.lot_id:
                    continue
                if line.lot_id.id in lot_ids:
                    raise ValidationError(_('Duplicate engine number %s found in the same transaction.') % line.lot_id.name)
                lot_ids.append(line.lot_id.id)
                
                # Check against other transactions
                other_line_id = self.env['tw.vehicle.ownership.handover.line'].search([
                    ('lot_id', '=', line.lot_id.id),
                    ('id', '!=', line.id),
                    ('ownership_handover_id.state', 'not in', ['cancel', 'draft']),
                    ('state', '!=', 'cancel')
                ], limit=1)
                if other_line_id:
                    raise ValidationError(_('Engine number %s has been given in %s') %
                                        (line.lot_id.name, other_line_id.ownership_handover_id.name))

                if not line.lot_id.vehicle_ownership_receipt_id:
                    raise ValidationError(_('Engine number %s has not been BPKB received') % line.lot_id.name)
                if not line.lot_id.birojasa_billing_date:
                    raise ValidationError(_('Engine number %s has not been Birojasa billing') % line.lot_id.name)
                if line.lot_id.vehicle_ownership_location_id.company_id.id != rec.company_id.id:
                    raise ValidationError(_('Engine number %s has not been at the same location') % line.lot_id.name)