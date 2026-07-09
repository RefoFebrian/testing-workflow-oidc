from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class TwVehicleOwnershipMutationRequestLine(models.Model):
    _name = "tw.ownership.mutation.request.line"
    _description = "Permohonan Mutasi BPKB Line"

    name = fields.Char(related="lot_id.name", store=True)
    state = fields.Selection(related="lot_id.state", store=True)
    
    ownership_mutation_request_id = fields.Many2one('tw.ownership.mutation.request', 
        string="Permohonan Mutasi BPKB", 
        ondelete='cascade',
        required=True)
        
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Engine No',
        required=True,
        domain="[('vehicle_ownership_number', '!=', False)]")
        
    bpkb_number = fields.Char(
        related='lot_id.vehicle_ownership_number',
        string='BPKB Number',
        store=True)
        
    customer_bpkb_id = fields.Many2one(
        related='lot_id.customer_stnk_id',
        string='Customer BPKB',
        store=True)
