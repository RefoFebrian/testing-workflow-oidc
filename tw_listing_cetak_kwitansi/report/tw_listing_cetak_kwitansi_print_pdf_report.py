# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from . import fungsi_terbilang

# 5: local imports

# 6: Import of unknown third party lib


class TwListingCetakKwitansiPrint(models.AbstractModel):
    _name = "report.tw_listing_cetak_kwitansi.tw_list_cetak_kwt_print"
    _description = "Report Listing Cetak Kwitansi Print PDF"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods

    # 14: private methods
    @api.model
    def _get_report_values(self, docids, data=None):
        model_name = 'tw.listing.cetak.kwitansi'
        trx_id = docids
        if not docids and data.get('context'):
            trx_id = data.get('context').get('active_id')
        if not trx_id and data.get('data'):
            trx_id = data.get('data').get('id')
        docs = self.env[model_name].sudo().browse(trx_id)
        
        return {
            'doc_ids': docids or [trx_id],
            'doc_model': model_name,
            'data': data.get('form'),
            'docs': docs,
            'company_id': self.env.company[0],
            'user': data.get('user'),
            'terbilang': self._terbilang
        }
    
    def _terbilang(self, amount):
        hasil = fungsi_terbilang.terbilang(amount, 'idr', 'id')
        return hasil