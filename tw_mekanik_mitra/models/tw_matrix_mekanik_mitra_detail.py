# 1: imports of python lib
from datetime import date, datetime, timedelta,time
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning, RedirectWarning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class MatrixMeknikMitraDetail(models.Model):
    _name = "tw.matrix.mekanik.mitra.detail"
    _description = "TW Matrix Mekanik Mitra Detail"

    # 7: defaults methods

    # 8: fields
    min_ue = fields.Float('Min UE')
    max_ue = fields.Float('Max UE')
    hari_kerja = fields.Float('Hari Kerja')
    jasa = fields.Float('Jasa')
    part = fields.Float('Part')

    # 9: relation fields
    matrix_id = fields.Many2one('tw.matrix.mekanik.mitra',ondelete='cascade')