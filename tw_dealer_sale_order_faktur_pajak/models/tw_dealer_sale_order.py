# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWFakturPajakDealerSaleOrder(models.Model):
    _name = "tw.dealer.sale.order"
    _inherit = ["tw.dealer.sale.order","tw.faktur.pajak.mixin"]

    faktur_pajak_id = fields.Many2one('tw.faktur.pajak', 'Generate Faktur Pajak')

    def scheduller_faktur_pajak(self,context=None):
        start_date = context.get('start_date',False)
        end_date = context.get('end_date',False)
        now = datetime.now().strftime('%Y-%m-%d')
        domain = []
        # domain = [
        #     ('state', 'in', ('progress', 'done')),
        #     ('faktur_pajak_id', '=', False),
        #     ('is_combined_tax', '=', False),
        #     ]
        if start_date:
            domain += [('date_order','>=',start_date),('date_order','<=',end_date or now)]
        # TODO: For testing
        dso_ids = self.search(domain, limit=30)
        if not dso_ids:
            return False
        for data in dso_ids:
            data.get_number_faktur_pajak()