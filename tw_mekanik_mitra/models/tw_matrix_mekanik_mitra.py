# 1: imports of python lib
from datetime import date, datetime, timedelta,time
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning, RedirectWarning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class MatrixMeknikMitra(models.Model):
    _name = "tw.matrix.mekanik.mitra"
    _description = "TW Matrix Mekanik Mitra"
    _rec_name = "company_id"
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    company_id = fields.Many2one('res.company','Branch')
    detail_ids = fields.One2many('tw.matrix.mekanik.mitra.detail','matrix_id')

    # 10: constraints & sql constraints
    @api.constrains('company_id')
    def _check_company_id_unique(self):
        for rec in self:
            duplicate = self.search([
                ('id', '!=', rec.id),
                ('company_id', '=', rec.company_id.id)
            ], limit=1)

            if duplicate:
                raise Warning(
                    "Master branch tidak boleh duplikat !"
                )
