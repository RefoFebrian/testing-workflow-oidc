from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]


class TwVehicleDocumentReceive(models.Model):
    _name = "tw.vehicle.document.receive"
    _description = "Penerimaan Faktur"
    _order = "id desc"

    name = fields.Char(string="Name", compute='_compute_name', store=True, default='New', copy=False)
    atpm_code = fields.Char(string='ATPM Code', required=False)
    date = fields.Date(string='Date', default=fields.Date.today())
    confirm_date = fields.Datetime('Posted on')
    cancel_date = fields.Datetime('Cancelled on')
    
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')

    partner_id = fields.Many2one(comodel_name='res.partner', string='Supplier')
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    company_id = fields.Many2one('res.company', string='Branch', required=True, domain=[('parent_id', '!=', False)], default=lambda self: self.env.company)
    vehicle_document_receive_line_ids = fields.One2many('tw.vehicle.document.receive.line', 'vehicle_document_receive_id', string="Detail", copy=True)
    domain_lot_ids = fields.Many2many('stock.lot', string='Engine No', compute='_compute_domain_lot_ids')

    @api.depends('company_id')
    def _compute_domain_lot_ids(self):
        for rec in self:
            if not rec.company_id:
                rec.domain_lot_ids = False
                continue
            query = """
                SELECT sl.id
                FROM stock_lot sl
                LEFT JOIN tw_vehicle_document_receive_line rl ON rl.lot_id = sl.id
                LEFT JOIN tw_vehicle_document_receive r ON r.id = rl.vehicle_document_receive_id
                WHERE sl.company_id = %s
                AND sl.vehicle_document_request_id IS NOT NULL
                AND sl.vehicle_document_receive_id IS NULL
                AND sl.cddb_state = 'cddb'
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_vehicle_document_receive_line rl2
                    JOIN tw_vehicle_document_receive r2 ON r2.id = rl2.vehicle_document_receive_id
                    WHERE rl2.lot_id = sl.id 
                    AND r2.state NOT IN ('done', 'cancel')
                    AND rl2.state != 'cancel'
                    AND r2.id != %s
                )
            """
        params = (rec.company_id.id, rec.id or 0)
        self._cr.execute(query, params)
        lot_ids = [res[0] for res in self._cr.fetchall() if res[0]]
        rec.domain_lot_ids = self.env['stock.lot'].browse(lot_ids) if lot_ids else False

    # Add the compute method
    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if hasattr(models, 'NewId') and isinstance(rec.id, models.NewId) or not rec.id:
                    rec.name = 'New'
                    continue
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('TF', str(rec.company_id.code))
    
    @api.onchange('company_id')
    def onchange_company(self):
        for rec in self:
            company_obj = rec.suspend_security().company_id
            rec.vehicle_document_receive_line_ids = False
            rec.partner_id = company_obj.default_supplier_id.id
            rec.atpm_code = company_obj.default_supplier_id.code

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.validate_order()
        return res

    def write(self, vals):
        res = super(TwVehicleDocumentReceive, self).write(vals)
        self.validate_order()
        return res

    def validate_order(self):
        for rec in self:
            if not rec.vehicle_document_receive_line_ids:
                raise ValidationError(_('Please input engine line.'))
            for line in rec.vehicle_document_receive_line_ids:
                other_line_id = self.env['tw.vehicle.document.receive.line'].search([
                    ('lot_id', '=', line.lot_id.id),
                    ('id', '!=', line.id),
                    ('vehicle_document_receive_id.state', '!=', 'cancel'),
                    ('state', '!=', 'cancel'),
                ], limit=1)
                if other_line_id:
                    raise ValidationError(_(f'Engine number {line.lot_id.name} has been processed in'
                                            f' {other_line_id.vehicle_document_receive_id.name}.'))
                if not line.lot_id.vehicle_document_request_id:
                    raise ValidationError(_(f'Engine number {line.lot_id.name} has not been requested (Permohonan Faktur).'))
                    
    def action_confirm(self):
        for rec in self.filtered(lambda r: r.state == 'draft'):
            rec.suspend_security().suspend_security().write({
                'state': 'done',
                'confirm_uid': self.env.user.id,
                'confirm_date': datetime.now(),
            })
            rec.vehicle_document_receive_line_ids.suspend_security().write(
                {'state': 'done'}
            )
            for line in rec.vehicle_document_receive_line_ids:
                line.lot_id.suspend_security().write({
                    'vehicle_document_receive_id': rec.id,
                    'vehicle_document_receive_date': rec.date,
                    'print_date': line.print_date,
                    'doc_number': line.doc_number,
                    'document_state': 'document_receive',
                })

    def action_cancel(self):
        for rec in self.filtered(lambda r: r.state == 'done'):
            rec.suspend_security().write({
                'state': 'cancel',
                'cancel_uid': self.env.user.id,
                'cancel_date': datetime.now(),
            })

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You cannot delete data that is not in draft status."))
