from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class registrationStockLotInherit(models.Model):
    _inherit = "stock.lot"

    registration_process_date = fields.Date(string='Tanggal Proses STNK', tracking=True)
    registration_process_id = fields.Many2one('tw.vehicle.registration.process', string="Proses STNK", tracking=True)