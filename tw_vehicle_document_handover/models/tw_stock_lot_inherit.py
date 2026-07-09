from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class documentHandoverLot(models.Model):
    _inherit = "stock.lot"

    notice_handover_date = fields.Date(string='Tgl Ambil Notice', tracking=True)
    registration_handover_date = fields.Date(string='Tgl Ambil STNK', tracking=True)
    plate_handover_date = fields.Date(string='Tgl Ambil No Polisi', tracking=True)
    ownership_handover_date = fields.Date(string='Penyerahan BPKB Date', tracking=True)
    registration_receiver = fields.Char(string='Penerima STNK', tracking=True)
    plate_receiver = fields.Char(string='Penerima No Polisi', tracking=True)
    ownership_receiver = fields.Char(string='Penerima BPKB', tracking=True)
    notice_receiver = fields.Char(string='Penerima Notice', tracking=True)
    
    registration_handover_id = fields.Many2one('tw.vehicle.registration.handover', string="Penyerahan STNK", tracking=True)
    notice_handover_id = fields.Many2one('tw.vehicle.registration.handover', string="Penyerahan Notice", tracking=True)
    plate_handover_id = fields.Many2one('tw.vehicle.registration.handover', string="Penyerahan Plate", tracking=True)
    ownership_handover_id = fields.Many2one('tw.vehicle.ownership.handover', string="Penyerahan BPKB", tracking=True)
