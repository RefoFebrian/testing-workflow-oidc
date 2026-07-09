# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritAccountMove(models.Model):
    _inherit = "account.move"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    # TODO : Hapus jika tidak diperlukan, jika diperlukan tolong confirm sebelum dihidupkan kembali
    # purchase_order_id = fields.Many2one(comodel_name='purchase.order', string='PO Number', help='Nomor PO Kendaraan')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    
