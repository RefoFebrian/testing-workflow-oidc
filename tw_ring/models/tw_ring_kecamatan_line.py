# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwRingKecamatanLine(models.Model):
    _name = "tw.ring.kecamatan.line"
    _description = "Master Ring Kecamatan Line"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    ring_kecamatan_id = fields.Many2one('tw.ring.kecamatan')
    ring_id = fields.Many2one('tw.ring', 'Ring Name', domain=[('active', '=', True)])
    city_id = fields.Many2one('res.city', 'Kota / Kab')
    district_id = fields.Many2one(comodel_name='res.district', string='Kecamatan', domain="[('city_id', '=', city_id)]")
    sub_district_id = fields.Many2one(comodel_name='res.sub.district', string='Kelurahan', domain="[('district_id', '=', district_id)]")

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('ring_kecamatan_line_unique', 'unique(city_id, district_id,sub_district_id, ring_kecamatan_id)', 'Ditemukan dengan kabupaten, kecamatan dan kelurahan yang sama dalam satu Ring Kecamatan!')
    ]

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods