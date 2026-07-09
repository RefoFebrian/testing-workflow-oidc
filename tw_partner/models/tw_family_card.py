from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TwFamilyCard(models.Model):
    _name = "tw.family.card"
    _description = 'Kartu Keluarga'

    name = fields.Char(
        string='Name',
        required=True)
    identification_id = fields.Char(
        string='NIK',
        required=False)
    birthdate = fields.Date(
        string='Tgl Lahir',
        required=False)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=False)
    relation_id = fields.Many2one('tw.selection', string='Hubungan', domain=[('type', '=', 'FamilyRelation')])
