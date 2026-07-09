# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class TwStockDocument(models.Model):
    """
    Stock Document model to track STNK/BPKB documents as line items of stock.lot.
    Each lot can have up to 2 stock documents: one for STNK and one for BPKB.
    """
    _name = "tw.stock.document"
    _description = "Stock Document (STNK/BPKB)"
    _order = "id desc"
    _rec_name = "display_name"

    # 7: defaults methods
    
    # 8: fields
    type = fields.Selection(selection=[('stnk', 'STNK'),('bpkb', 'BPKB'),],string='Document Type',)
    state = fields.Selection(selection=[
        ('stock', 'Stock'),
        ('intransit', 'In Transit'),
        ('customer', 'Customer'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='stock',)
    document_number = fields.Char(string='Document Number',help='STNK or BPKB number')
    display_name = fields.Char(compute='_compute_display_name',store=True)

    # 9: relation fields
    lot_id = fields.Many2one('stock.lot',string='Engine Number',ondelete='cascade')
    location_id = fields.Many2one('tw.vehicle.document.location',string='Document Location')
    company_id = fields.Many2one('res.company',string='Branch',default=lambda self: self.env.company)
    product_id = fields.Many2one(related='lot_id.product_id',string='Product',store=True)
    move_ids = fields.Many2many(
        comodel_name='tw.vehicle.document.move',
        string='Document Moves',
        compute='_compute_move_ids',
    )
    move_count = fields.Integer(
        compute='_compute_move_ids',
        string='Move Count',
    )

    # Audit Trail
    last_update_date = fields.Datetime(string='Last Updated',default=fields.Datetime.now)
    last_update_uid = fields.Many2one('res.users',string='Last Updated By',default=lambda self: self.env.user)

    # 10: constraints & sql constraints
    _sql_constraints = [
        (
            'unique_lot_type',
            'UNIQUE(lot_id, type)',
            'A document of this type already exists for this lot!'
        ),
    ]

    # 11: compute/depends & on change methods
    @api.depends('lot_id', 'type', 'document_number')
    def _compute_display_name(self):
        """Compute display name: [Type] Lot Name - Document Number"""
        for rec in self:
            type_label = dict(self._fields['type'].selection).get(rec.type, '')
            doc_num = rec.document_number or 'No Number'
            lot_name = rec.lot_id.name or ''
            rec.display_name = f"[{type_label}] {lot_name} - {doc_num}"

    @api.depends('lot_id', 'type')
    def _compute_move_ids(self):
        """Compute move history based on lot_id and document type"""
        move_model = self.env['tw.vehicle.document.move']
        for rec in self:
            if not rec.lot_id or not rec.type:
                rec.move_ids = False
                rec.move_count = 0
                continue
            # Map type to document_type in move model
            doc_type = 'vehicle_registration' if rec.type == 'stnk' else 'vehicle_ownership'
            moves = move_model.search([
                ('lot_id', '=', rec.lot_id.id),
                ('document_type', '=', doc_type),
            ])
            rec.move_ids = moves
            rec.move_count = len(moves)

    @api.constrains('lot_id', 'type')
    def _check_unique_document(self):
        """Ensure each lot has at most one STNK and one BPKB document"""
        for rec in self:
            existing = self.search([
                ('lot_id', '=', rec.lot_id.id),
                ('type', '=', rec.type),
                ('id', '!=', rec.id),
            ], limit=1)
            if existing:
                raise ValidationError(
                    _('A %s document already exists for lot %s!') % 
                    (rec.type.upper(), rec.lot_id.name)
                )

    # 12: override methods
    def write(self, vals):
        """Override write to update audit trail"""
        vals['last_update_date'] = fields.Datetime.now()
        vals['last_update_uid'] = self.env.user.id
        return super(TwStockDocument, self).write(vals)

    # 13: action methods
    def action_set_stock(self):
        """Set document state to stock"""
        self.write({'state': 'stock'})

    def action_set_intransit(self):
        """Set document state to in transit"""
        self.write({'state': 'intransit'})

    def action_set_customer(self):
        """Set document state to customer (handed over)"""
        self.write({'state': 'customer'})

    def action_cancel_receipt(self):
        """
        Global cancel method for STNK/BPKB receipt cancellation.

        Resets the document state to 'cancelled' and clears document number
        and location to indicate the document is no longer received/valid.
        Called by STNK and BPKB receipt cancel actions.
        """
        self.suspend_security().write({
            'state': 'cancelled',
            'document_number': False,
            'location_id': False,
            'company_id': False,
        })

    def action_view_moves(self):
        """Open document move history"""
        self.ensure_one()
        doc_type = 'vehicle_registration' if self.type == 'stnk' else 'vehicle_ownership'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Document Moves'),
            'res_model': 'tw.vehicle.document.move',
            'view_mode': 'list,form',
            'domain': [
                ('lot_id', '=', self.lot_id.id),
                ('document_type', '=', doc_type),
            ],
            'context': {
                'default_lot_id': self.lot_id.id,
                'default_document_type': doc_type,
            },
        }

    # 14: private methods
    def update_location(self, location_id):
        """
        Update document location.
        
        :param location_id: ID of tw.vehicle.document.location
        """
        self.write({'location_id': location_id})
