# 3: imports of odoo
from odoo import models, api


class MutasiAssetBaksoReport(models.AbstractModel):
    _name = "report.tw_asset_mutation.berita_acara_mutasi_asset_print"
    _description = "Berita Acara Mutasi Asset"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.asset.distribution'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'tw.asset.distribution',
            'docs': docs,
        }