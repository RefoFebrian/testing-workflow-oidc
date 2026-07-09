# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwStockOpnameDirectGiftPrintBaksoReport(models.AbstractModel):
    _name = "report.tw_stock_opname_direct_gift.so_dg_bakso"
    _description = "Direct Gift Bakso Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.stock.opname.direct.gift'].suspend_security().browse(data.get('ids', docids))

        return {
            'doc_ids': docs.ids,
            'doc_model': 'tw.stock.opname.direct.gift',
            'data': data,
            'docs': docs,
            'company_id': self.env.company,
        }
