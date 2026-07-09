# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, AccessError

# 5: local imports

# 6: Import of unknown third party lib

class PartnerHistory(models.Model):
    _name = "tw.partner.history"
    _description = "Partner History"

    # 7: defaults methods

    # 8: fields
    description = fields.Char(string='Keterangan', required=True)
    before_update = fields.Char(string='Sebelum Update')
    after_update = fields.Char(string='Setelah Update')
    origin = fields.Char(string='Origin', required=True)
    
    # 9: relation fields
    partner_id = fields.Many2one('res.partner', string='Partner')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods

                