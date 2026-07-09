from odoo import models, api

class PrintPeminjamanAset(models.AbstractModel):
    _name = "report.tw_asset_lending_return_approval.print_lending"
    _description = "Report Peminjaman Aset"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.asset.lending'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'tw.asset.lending',
            'docs': docs,
        }