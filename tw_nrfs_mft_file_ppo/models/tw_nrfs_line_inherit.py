# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
import odoo.addons.base.models.decimal_precision as dp

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritNrfsLineMFT(models.Model):
    _inherit = "tw.nrfs.line"
    
    # 7: defaults methods

    # 8: fields
    urgent_po_number = fields.Char(string='No PO Urgent MD', size=50)
    urgent_po_date = fields.Date(string='Tanggal PO Urgent')
    is_urgent_po = fields.Boolean(string='Dipenuhi dengan PO Urgent?', default=False)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('handling_id')
    def _change_is_urgent_po(self):
        self.is_urgent_po = False
        if self.handling_id and self.handling_id.id == self.env.ref('tw_nrfs.nrfs_penanganan_unit_part_pesan_urgent').id:
            self.is_urgent_po = True

    # 12: override methods

    # 13: action methods

    # 14: private methods
    
    