# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class TwRemark(models.Model):
    """
    Master data untuk Remark pada report dan dokumen.
    
    Remark ditentukan berdasarkan form/model transaksi yang digunakan,
    sehingga setiap model transaksi memiliki remark yang berbeda.
    
    Fields:
        model_id: Model/Form yang menggunakan remark ini.
        remark: Isi teks remark yang akan ditampilkan.
    """
    _name = "tw.remark"
    _description = 'Remark'
    _rec_name = 'remark'
    _order = 'model_id asc'
    
    model_id = fields.Many2one(
        'ir.model', 
        string="Form Name",
        domain="[('model','in',('tw.asset.disposal','tw.faktur.pajak.gabungan','tw.account.payment','tw.work.order','tw.dealer.sale.order'))]",
        required=True,
        ondelete='cascade'
    )
    remark = fields.Char(string="Remark", required=True)
    
    _sql_constraints = [
        ('unique_model_id', 'unique(model_id)', 'Master data cannot be duplicate!')
    ]
