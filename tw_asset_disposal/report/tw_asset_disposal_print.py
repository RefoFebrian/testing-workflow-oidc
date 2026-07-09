# 3: imports of odoo
from odoo import models, api


class ReportDisposalAssetPrint(models.AbstractModel):
    _name = "report.tw_asset_disposal.report_disposal_asset_print"
    _description = "Laporan Form Disposal Asset"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.asset.disposal'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'tw.asset.disposal',
            'docs': docs,
        }