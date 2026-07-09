# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class TwStockOpnameAssetBasoWizard(models.TransientModel):
    _name = "tw.stock.opname.asset.baso.wizard"
    _description = "Stock Opname Asset BASO Wizard"

    note_bakso = fields.Text('Note')
    opname_id = fields.Many2one('tw.stock.opname.asset', 'Stock Opname', readonly=True)

    def action_submit(self):
        """
        Menyimpan catatan dan memanggil laporan QWeb pada 'opname_id'.
        Ini adalah cara Odoo 18, tidak perlu membuat 'datas' dict manual.
        """
        self.ensure_one()
        
        # 1. Simpan catatan dari wizard ke record SO Asset
        self.opname_id.note_bakso = self.note_bakso
        
       
        return self.env.ref('tw_stock_opname_asset.action_print_bakso_stock_opname_asset').report_action(self.opname_id)