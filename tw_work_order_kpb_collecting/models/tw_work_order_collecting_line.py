# -*- coding: utf-8 -*-

# 1: imports of python lib
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderCollectingLine(models.Model):
    _inherit = "tw.work.order.collecting.line"
    # 7: defaults methods

    # 8: fields
    kpb_ke = fields.Char('KPB Ke')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods