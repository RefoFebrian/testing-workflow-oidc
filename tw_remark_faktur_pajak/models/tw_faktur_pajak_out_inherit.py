# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class TwFakturPajakOutInherit(models.Model):
    """
    Inherit tw.faktur.pajak.out untuk menambahkan fungsionalitas remark.
    Menambahkan computed field remark dan helper method untuk mendapatkan remark
    berdasarkan model transaksi.
    """
    _inherit = "tw.faktur.pajak.out"
    
    remark = fields.Char(
        string='Remark',
        compute='_compute_remark',
        store=True,
        help="Remark berdasarkan model transaksi yang digunakan."
    )
    
    @api.depends('model_id')
    def _compute_remark(self):
        """
        Compute remark berdasarkan model_id dari transaksi.
        Mencari remark di master tw.remark berdasarkan model yang sama.
        """
        for record in self:
            remark = ''
            if record.model_id:
                remark_obj = self.env['tw.remark'].search([
                    ('model_id', '=', record.model_id.id)
                ], limit=1)
                if remark_obj:
                    remark = remark_obj.remark
            record.remark = remark
    
    def get_remark_by_model(self, model_name):
        """
        Helper method untuk mendapatkan remark berdasarkan nama model.
        
        Args:
            model_name: Nama model (e.g., 'tw.work.order', 'tw.dealer.sale.order')
            
        Returns:
            String remark atau empty string jika tidak ditemukan.
        """
        model_obj = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
        if model_obj:
            remark_obj = self.env['tw.remark'].search([
                ('model_id', '=', model_obj.id)
            ], limit=1)
            if remark_obj:
                return remark_obj.remark
        return ''
