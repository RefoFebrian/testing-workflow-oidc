from odoo import models, fields, api

class JadwalPengiriman(models.Model):
    _inherit = "res.partner"

    jadwal_hari_pengiriman = fields.Selection([
        ('senin', 'Senin'),
        ('selasa', 'Selasa'),
        ('rabu', 'Rabu'),
        ('kamis', 'Kamis'),
        ('jumat', 'Jumat'),
        ('sabtu', 'Sabtu'),
        ('minggu', 'Minggu'),
    ],string='Hari Pengiriman Sparepart')
    dealer_group_id =  fields.Many2one(comodel_name='tw.selection', string='Dealer Group' , domain=[('type','=','DealerGroup')], help="Used to Group Several Dealers into 1 Group.")