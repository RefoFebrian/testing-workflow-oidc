# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class LeadLog(models.Model):

    _name = "tw.lead.logs"
    _description = "Lead Log"
    _order = "date asc"

    # 7: defaults methods
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char( required=True, string="Name",  help="")
    date  = fields.Datetime(string='Date', default=_get_default_datetime)

    # 9: relation fields
    lead_id = fields.Many2one(comodel_name='tw.lead', string='Lead')
    category_id = fields.Many2one(comodel_name='tw.selection', string='Category', domain="[('type', '=', 'LogCategory')]", help='')
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
