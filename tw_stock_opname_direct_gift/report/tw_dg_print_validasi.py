# 1: Imports of Python lib
import datetime

# 2: Imports of known third party lib

# 3: Imports of Odoo
from odoo import models, api, _, fields

# 4: Imports from Odoo modules
from odoo.exceptions import UserError as Warning

# 5: Local imports

# 6: Imports of unknown third party lib


class TwDgPrintValidasi(models.AbstractModel):
    _name = "report.tw_stock_opname_direct_gift.dg_print_validasi"
    _description = "Direct Gift Validasi Report"

    def get_local_time(self):
        return fields.Datetime.context_timestamp(self, datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S')

    @api.model
    def _get_report_values(self, docids, data=None):
        if data and 'ids' in data:
            doc_ids = data['ids']
        else:
            doc_ids = docids

        docs = self.env['tw.stock.opname.direct.gift'].suspend_security().browse(doc_ids)

        return {
            'doc_ids': docs.ids,
            'doc_model': 'tw.stock.opname.direct.gift',
            'data': data,
            'docs': docs,
            'company_id': self.env.company,
            'get_branch': lambda d: d.get('company_id'),
            'get_name': lambda d: d.get('name'),
            'get_division': lambda d: d.get('division'),
            'get_tgl_so': lambda d: d.get('tgl_so'),
            'get_pdi': lambda d: d.get('pdi_id'),
            'get_adh': lambda d: d.get('adh_id'),
            'get_soh': lambda d: d.get('soh_id'),
            'get_user': lambda d: d.get('user'),
            'get_date': lambda d: d.get('date'),
            'get_detail': lambda d: d.get('detail_ids'),
            'get_other_dg': lambda d: d.get('other_dg_ids'),
            'get_local_time': self.get_local_time,
        }
