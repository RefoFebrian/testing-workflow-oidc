# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwAssetAcquisitionUser(models.Model):
    """
    Model untuk menyimpan data pengguna asset dan serial number.
    Satu record = satu unit asset yang akan dibuat.
    
    Contoh: GR Laptop qty=5 maka akan ada 5 record di model ini,
    masing-masing dengan employee_id dan serial_number berbeda.
    """
    _name = "tw.asset.acquisition.user"
    _description = "Asset Acquisition User Line"
    _order = "sequence, id"

    # 7: defaults methods
    
    # 8: fields
    sequence = fields.Integer('Sequence', default=10)
    serial_number = fields.Char('Serial Number', help="Nomor serial unit asset (freetext)")
    
    # 9: relation fields
    acquisition_id = fields.Many2one(
        comodel_name='tw.asset.acquisition',
        string='Acquisition',
        required=True,
        ondelete='cascade'
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Pengguna Asset',
        required=True,
        help="Employee yang akan menjadi pengguna asset"
    )
    asset_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Created Asset',
        readonly=True,
        help="Asset yang dibuat dari line ini setelah confirm"
    )
    
    # Related fields from acquisition
    company_id = fields.Many2one(related='acquisition_id.company_id', store=True)
    product_id = fields.Many2one(related='acquisition_id.good_receive_line_id.product_id', store=True)
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
