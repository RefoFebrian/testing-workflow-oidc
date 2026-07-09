# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime
from optparse import Values

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class TwLeadStages(models.Model):
    _name = "tw.lead.stages"
    _inherit = "crm.stage"
    _description = "Lead Stages"
