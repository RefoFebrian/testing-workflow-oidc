# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwMasterModelPajak(models.Model):
    """
    Model ini mendaftarkan model-model yang diizinkan 
    untuk proses Faktur Pajak Gabungan.
    """
    _name = "tw.master.model.pajak"
    _description = "Master Model untuk Faktur Pajak Gabungan"
    
    # 7: default methods

    # 8: fields
    name = fields.Char(
        string="Nama Model", 
        required=True, 
        help="Nama yang mudah dibaca, misal: 'Dealer Sale Order'"
    )
    module_name = fields.Char(
        string="Nama Modul Jembatan", 
        required=True, 
        help="Nama teknis modul jembatan Coretax yang wajib ter-install, misal: tw_dealer_sale_order_faktur_pajak"
    )
    model_name = fields.Char(
        string="Nama Teknis Model", 
        related="model_id.model", 
        readonly=True,
        store=True
    )
    
    
    # 9: relation fields
    model_id = fields.Many2one(
        'ir.model', 
        string="Model Teknis", 
        required=True, 
        domain=[('transient', '=', False)],
        ondelete='cascade',
        help="Model teknis Odoo, misal: tw.dealer.sale.order"
    )

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('model_name_uniq', 'unique(model_name)', 'Model teknis tidak boleh duplikat!')
    ]