# 1: Imports of Python lib
import datetime

# 2: Imports of known third party lib

# 3: Imports of Odoo
from odoo import models, api, _, fields

# 4: Imports from Odoo modules
from odoo.exceptions import UserError as Warning

# 5: Local imports

# 6: Imports of unknown third party lib


class TwStockOpnameBpkbPrintValidasi(models.AbstractModel):
    _name = "report.tw_vehicle_document_stock_opname.bpkb_print_validasi"
    _description = "Stock Opname BPKB Validasi Report"

    def get_local_time(self):
        return fields.Datetime.context_timestamp(self, datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S')


    @api.model
    def _get_report_values(self, docids, data=None):
        if data and 'ids' in data:
            doc_ids = data['ids']
        else:
            doc_ids = docids

        docs = self.env['tw.vehicle.document.stock.opname'].suspend_security().browse(doc_ids)

        return {
            'doc_ids': docs.ids,
            'doc_model': 'tw.vehicle.document.stock.opname',
            'data': data,
            'docs': docs,
            'company_id': self.env.company,
            'get_branch': lambda d: d.get('company_id'),
            'get_name': lambda d: d.get('name'),
            'get_division': lambda d: d.get('division'),
            'get_tgl_so': lambda d: d.get('tgl_so'),
            'get_staff_bbn': lambda d: d.get('staff_bbn_id'),
            'get_adh': lambda d: d.get('adh_id'),
            'get_soh': lambda d: d.get('soh_id'),
            'get_user': lambda d: d.get('user'),
            'get_date': lambda d: d.get('date'),
            'get_detail': lambda d: d.get('detail_ids'),
            'get_bpkb_other': lambda d: d.get('other_bpkb_ids'),
            'get_local_time': self.get_local_time,
        }
