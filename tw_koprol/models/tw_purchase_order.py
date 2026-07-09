from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning
import requests

class InheritTedsPurchaseOrderKoprol(models.Model):
    _inherit = "purchase.order.asset"

    last_modified_date = fields.Datetime('Last Modified Date Koprol')

      
    def action_check_status(self):
        if self.reference:
            config = self.env['tw.api.configuration'].sudo().search([('name', '=', 'Koprol Integration'),('code','=','koprol')],limit=1)
            if not config:
                raise Warning('Configuration Koprol belum di setting !')
            data = config.check_status_koprol(
                {
                    'purchase_order_no_erp': self.name,
                    'purchase_order_no_koprol': self.reference,
                    'purchase_order_status': self.state,
                    'last_modified_erp': self.write_date
                
                }
                )
            transaction_no = data.get('purchase_order_no_erp')
            transaction_status = data.get('purchase_order_status')
            if self.name != transaction_no:
                raise Warning('Transaksi PO yang di dapat %s tidak sesuai dengan nomor transaksi PO %s dengan status %s' % (transaction_no,self.name,transaction_status))

