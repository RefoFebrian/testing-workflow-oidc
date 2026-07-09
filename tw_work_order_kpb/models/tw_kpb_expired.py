# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class TwKpbExpired(models.Model):
    _name = "tw.kpb.expired"
    _description = "TW KPB Expired"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Engine Code', required=True)
    description = fields.Char(string='Description', required=True)
    hari = fields.Integer(string='Hari', required=True)
    km = fields.Integer(string='Km', required=True)
    service = fields.Selection(
        selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')],
        string='Service',
        required=True
    )

    # 9: relation fields

    # 10: constraints & sql constraints
    @api.constrains('name', 'service')
    def _check_unique_service(self):
        for record in self:
            duplicate = self.search([
                ('name', '=', record.name),
                ('service', '=', record.service),
                ('id', '!=', record.id)  # Hindari pengecekan pada record yang sedang diedit
            ])
            if duplicate:
                raise ValidationError('Engine Sudah Terdaftar!')

    # 11: compute/depends & on change methods

    # 12: override methods   
