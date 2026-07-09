from odoo import models, fields

class JadwalPengiriman(models.Model):
    _inherit = "res.partner"

    rl_permata_number = fields.Char('Nomor RL Permata')
    rl_bri_number = fields.Char('Nomor RL BRI')
