# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwStockOpnameBpkbPrintBaksoReport(models.AbstractModel):
    _name = "report.tw_vehicle_document_stock_opname.so_bpkb_bakso"
    _description = "Stock Opname BPKB Bakso Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.vehicle.document.stock.opname'].suspend_security().browse(data.get('ids', docids))

        return {
            'doc_ids': docs.ids,
            'doc_model': 'tw.vehicle.document.stock.opname',
            'data': data,
            'docs': docs,
            'company_id': self.env.company,
        }
