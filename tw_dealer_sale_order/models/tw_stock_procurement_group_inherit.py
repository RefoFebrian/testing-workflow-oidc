# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools.sql import column_exists, create_column

# 5: local imports

# 6: Import of unknown third party lib

class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    dealer_sale_order_id = fields.Many2one('tw.dealer.sale.order', 'Dealer Sale Order')
