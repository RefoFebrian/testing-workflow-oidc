# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning


# 5: local imports

# 6: Import of unknown third party lib


class TwVehicleDocumentMove(models.Model):
    _name = "tw.vehicle.document.move"
    _description = "Vehicle Document Move" 

    # 7: Fields
    reference = fields.Char(string='Reference', help='Reference to source transaction (e.g., PST/001, MUS/001)')
    document_number = fields.Char(string='Document Number', help='STNK or BPKB number')
    document_type = fields.Selection([
        ('vehicle_registration', 'STNK'),
        ('vehicle_ownership', 'BPKB'),
    ], string='Document Type', required=True)
    date = fields.Date(string='Move Date', default=fields.Date.context_today, required=True)

    # 8: Relation Fields
    company_id = fields.Many2one('res.company', string="Branch", required=True, default=lambda self: self.env.company)
    source_location_id = fields.Many2one('tw.vehicle.document.location', string='Source Location', domain="[('type', '=', 'internal'), ('active', '=', True), ('document_type', '=', document_type)]")
    destination_location_id = fields.Many2one('tw.vehicle.document.location', string='Destination Location', domain="[('type', '=', 'internal'), ('active', '=', True), ('document_type', '=', document_type)]")
    lot_id = fields.Many2one('stock.lot', string='Vehicle (Engine Number)', required=True, ondelete='restrict')

    # 9: Private Methods
    @api.model
    def _create_document_move(self, vals):
        """
        Private method to create vehicle document move record.
        Can be called from any transaction that needs to track document movement.
        
        :param vals: Dictionary containing move data
            - reference (str): Source transaction reference
            - date (date): Move date
            - document_type (str): 'vehicle_registration' or 'vehicle_ownership'
            - document_number (str): STNK/BPKB number
            - lot_id (int): Vehicle ID
            - source_location_id (int, optional): Source location ID
            - destination_location_id (int, optional): Destination location ID
            - company_id (int): Company ID
        :return: Created move record
        """
        return self.sudo().create(vals)