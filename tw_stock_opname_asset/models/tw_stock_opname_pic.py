# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TWStockOpnameAssetPic(models.Model):
    _name = "tw.stock.opname.asset.pic"
    _description = "TW Stock Opname Asset PIC"

    job_id = fields.Many2one('hr.job','Job')

    _sql_constraints = [('unique_job', 'unique(job_id)', 'Job sudah ada !')]