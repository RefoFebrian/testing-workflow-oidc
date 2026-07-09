from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]


class TwVehicleDocumentRequest(models.Model):
    _name = "tw.vehicle.document.request"
    _description = "Permohonan Faktur"
    _order = "id desc"

    name = fields.Char(string="Name", readonly=True, default='New', copy=False, compute='_compute_name', store=True)
    atpm_code = fields.Char(string='AHM Code')
    is_exception_faktur = fields.Boolean(string='Exception Faktur',help='Jika tidak memiliki faktur Fisik, tetapi tetap mau di jalankan')
    date = fields.Date(string='Date', default=fields.Date.today())
    confirm_date = fields.Datetime('Posted on')
    cancel_date = fields.Datetime('Cancelled on')
    
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')
    
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Supplier', required=False)
    company_id = fields.Many2one('res.company', string='Branch', required=True, domain=[('parent_id', '!=', False)], default=lambda self: self.env.company)
    vehicle_document_request_line_ids = fields.One2many('tw.vehicle.document.request.line', 'vehicle_document_request_id', string="Vehicle Document Request Line", copy=True)

    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if hasattr(models, 'NewId') and isinstance(rec.id, models.NewId) or not rec.id:
                    rec.name = 'New'
                    continue
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('PF', str(rec.company_id.code))

    @api.onchange('company_id')
    def onchange_company(self):
        self.vehicle_document_request_line_ids = False
        transaction_id = ''
        if self._origin.id:
            transaction_id = f" AND r2.id != {self._origin.id}"
        
        query = f"""
            SELECT DISTINCT sl.id
            FROM stock_lot sl
            LEFT JOIN tw_vehicle_document_request_line rl ON rl.lot_id = sl.id
            LEFT JOIN tw_vehicle_document_request r ON r.id = rl.vehicle_document_request_id
            WHERE sl.company_id = {self.company_id.id}
            AND sl.cddb_state = 'cddb'
            AND sl.vehicle_document_request_id IS NULL
            AND NOT EXISTS (
                SELECT 1 
                FROM tw_vehicle_document_request_line rl2
                JOIN tw_vehicle_document_request r2 ON r2.id = rl2.vehicle_document_request_id
                WHERE rl2.lot_id = sl.id 
                AND r2.state NOT IN ('cancel','done')
                AND rl2.state != 'cancel'
                {transaction_id}
            )
        """
        self._cr.execute(query)
        lot_ids = [rec[0] for rec in self._cr.fetchall()]
        
        company_obj = self.suspend_security().company_id
        self.vehicle_document_request_line_ids = [(0, 0, {'lot_id': lot_id}) for lot_id in lot_ids]
        self.partner_id = company_obj.default_supplier_id.id
        self.atpm_code = company_obj.default_supplier_id.code

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._validate_order()
        return res

    def write(self, vals):
        res = super(TwVehicleDocumentRequest, self).write(vals)
        self._validate_order()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You cannot delete data that is not in draft status."))
    
    def action_confirm(self):
        for rec in self.filtered(lambda r: r.state in self._validate_state_confirm()):
            rec.write({
                'state': 'done',
                'confirm_uid': self.env.user.id,
                'confirm_date': datetime.now(),
            })
            rec.vehicle_document_request_line_ids.suspend_security().write(
                {'state': 'done'}
            )
            lot_ids = rec.vehicle_document_request_line_ids.mapped('lot_id')
            lot_ids.write({
                'vehicle_document_request_id': rec.id,
                'vehicle_document_request_date': rec.date,
                'document_state': 'document_request',
            })

    def action_cancel(self):
        for rec in self.filtered(lambda r: r.state == 'done'):
            rec.write({
                'state': 'cancel',
                'cancel_uid': self.env.user.id,
                'cancel_date': datetime.now(),
            })
    
    def _validate_order(self):
        for rec in self:
            if not rec.vehicle_document_request_line_ids:
                raise ValidationError(_('Please input engine line.'))
            for line in rec.vehicle_document_request_line_ids:
                other_line_id = self.env['tw.vehicle.document.request.line'].search([
                    ('lot_id', '=', line.lot_id.id),
                    ('id', '!=', line.id),
                    ('vehicle_document_request_id.state', '!=', 'cancel'),
                    ('state', '!=', 'cancel'),
                ], limit=1)
                if other_line_id:
                    raise ValidationError(_(f'Engine number {line.lot_id.name} has been processed in'
                                            f' {other_line_id.vehicle_document_request_id.name}.'))
                if line.lot_id.cddb_state != 'cddb':
                    raise ValidationError(_(f'State of Engine number {line.lot_id.name} is not in CDDB OK.'))

    def _validate_state_confirm(self):
        return ['draft']