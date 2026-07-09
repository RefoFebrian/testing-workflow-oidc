# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
import odoo.addons.base.models.decimal_precision as dp

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWNrfsLineStock(models.Model):
    _name = "tw.nrfs.line.stock"
    _description = "NRFS - Stok Sparepart"

    qty_stock = fields.Float(string='Qty Stock', digits='Product Unit of Measure')
    qty_intransit_in = fields.Float(string='Qty Intransit IN', digits='Product Unit of Measure')
    line_id = fields.Many2one('tw.nrfs.line', 'ID Case NRFS', ondelete='cascade')
    company_id = fields.Many2one('res.company', string="Branch")