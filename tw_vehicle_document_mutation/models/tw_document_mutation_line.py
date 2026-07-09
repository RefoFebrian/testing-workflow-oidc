from odoo import api, fields, models, _

class TwDocumentMutationLine(models.Model):
    _name = "tw.document.mutation.line"
    _description = "Document Mutation Line"
    _order = "id desc"

    mutation_id = fields.Many2one(
        'tw.document.mutation',
        string='Mutation',
        required=True,
        ondelete='cascade'
    )
    
    lot_id = fields.Many2one(
        'stock.lot',
        string='Engine Number',
    )
    
    chassis_number = fields.Char(
        string='Chassis Number',
        related='lot_id.chassis_number',
        readonly=True,
        store=True
    )
    
    document_number = fields.Char(
        string='Document Number',
        compute='_compute_document_number',
        store=True
    )
    
    stnk_current_location_id = fields.Many2one(
        comodel_name='tw.vehicle.document.location',
        string='STNK Current Location',
        compute='_compute_current_location',
        store=True
    )
    
    bpkb_current_location_id = fields.Many2one(
        'tw.vehicle.document.location',
        string='BPKB Current Location',
        compute='_compute_current_location',
        store=True
    )
    
    @api.depends('lot_id', 'mutation_id.document_type')
    def _compute_document_number(self):
        for line in self:
            if line.lot_id and line.mutation_id.document_type == 'stnk':
                line.document_number = line.lot_id.vehicle_registration_number
            elif line.lot_id and line.mutation_id.document_type == 'bpkb':
                line.document_number = line.lot_id.vehicle_ownership_number
            else:
                line.document_number = False
    
    @api.depends('lot_id', 'mutation_id.document_type')
    def _compute_current_location(self):
        for line in self:
            if line.lot_id and line.mutation_id.document_type == 'stnk':
                line.stnk_current_location_id = line.lot_id.vehicle_registration_location_id
                line.bpkb_current_location_id = False
            elif line.lot_id and line.mutation_id.document_type == 'bpkb':
                line.bpkb_current_location_id = line.lot_id.vehicle_ownership_location_id
                line.stnk_current_location_id = False
            else:
                line.stnk_current_location_id = False
                line.bpkb_current_location_id = False