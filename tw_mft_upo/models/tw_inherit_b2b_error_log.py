# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import math

# 2: import of known third party lib
import xlrd
import base64

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritTwB2bErrorLog(models.Model):
    _inherit = "tw.b2b.error.log"

    # 7: defaults methods
    
    # 8: fields
    
    # Audit Trail
    
    # 9: relation fields

    p2p_id = fields.Many2one('tw.p2p.purchase.order', string="P2P Purchase Order", help="P2P Purchase Order")