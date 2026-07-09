from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    _inherit = "stock.lot"

    notice_receipt_date = fields.Date(string='Tanggal Terima Notice', tracking=True)
    notice_date = fields.Date(string='Tanggal Notice', tracking=True)
    stnk_date = fields.Date(string='Tanggal JTP STNK', tracking=True)
    vehicle_registration_receipt_date = fields.Date(string='Tanggal Terima STNK', tracking=True)
    plate_receipt_date = fields.Date(string='Tanggal Terima Plat', tracking=True)
    notice_number = fields.Char(string='Nomor Notice', copy=False, tracking=True)
    vehicle_registration_number = fields.Char(string='Nomor STNK', copy=False, tracking=True)
    plate_number = fields.Char(string='Nomor Plat', copy=False, tracking=True)
    vehicle_ownership_receipt_date = fields.Date(string='Tanggal Terima BPKB', copy=False, tracking=True)
    vehicle_ownership_date = fields.Date(string='Tanggal BPKB', copy=False, tracking=True)
    vehicle_ownership_number = fields.Char(string='Nomor BPKB', copy=False, tracking=True)
    vehicle_ownership_order_number = fields.Char(string='Nomor Urut BPKB', copy=False, tracking=True)

    notice_receipt_id = fields.Many2one('tw.vehicle.registration.receipt', string="Terima Notice", readonly=True, tracking=True)
    vehicle_registration_receipt_id = fields.Many2one('tw.vehicle.registration.receipt', string="Terima STNK", readonly=True, tracking=True)
    plate_receipt_id = fields.Many2one('tw.vehicle.registration.receipt', string="Terima Plat", readonly=True, tracking=True)
    vehicle_ownership_receipt_id = fields.Many2one('tw.vehicle.ownership.receipt', string="Terima BPKB", readonly=True, tracking=True)
    vehicle_registration_location_id = fields.Many2one('tw.vehicle.document.location', string="Lokasi STNK", domain=[('document_type', '=', 'vehicle_registration')], tracking=True)
    vehicle_ownership_location_id = fields.Many2one('tw.vehicle.document.location', string="Lokasi BPKB", domain=[('document_type', '=', 'vehicle_ownership')], tracking=True)

    