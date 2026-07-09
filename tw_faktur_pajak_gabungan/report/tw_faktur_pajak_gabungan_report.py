# 1: imports of python lib
from datetime import datetime

# 3: imports of odoo
from odoo import models, api

# 6: Import of unknown third party lib
import pytz


class ReportFakturPajakGabungan(models.AbstractModel):
    _name = "report.tw_faktur_pajak_gabungan.report_faktur_pajak_gabungan"
    _description = "Laporan Faktur Pajak Gabungan"

    def get_local_date(self):
        user = self.env.user
        now_utc = datetime.now(pytz.utc)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now_local = now_utc.astimezone(tz)
        return now_local.strftime("%Y-%m-%d")

    def get_division_label(self, division):
        if division == 'Unit':
            return "PENJUALAN SEPEDA MOTOR HONDA (PERINCIAN TERLAMPIR)"
        elif division == 'Sparepart':
            return "PENJUALAN SPAREPART HONDA (PERINCIAN TERLAMPIR)"
        return division or ''

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.faktur.pajak.gabungan'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'tw.faktur.pajak.gabungan',
            'docs': docs,
            'get_local_date': self.get_local_date,
            'get_division_label': self.get_division_label,
        }
