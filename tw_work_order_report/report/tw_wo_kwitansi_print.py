# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4: imports from odoo modules

# 5: local imports
from . import fungsi_terbilang

# 6: Import of unknown third party lib


class PrintWorkOrderKwitansi(models.AbstractModel):
    _name = "report.tw_work_order_report.print_wo_kwitansi"
    _description = "Work Order Print Kwitansi"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_kwitansi_lines(self, wo):
        """Cari payment lines yang terkait dengan Work Order ini."""
        payment_lines = self.env['tw.account.payment.line'].suspend_security().search([
            ('move_line_id.ref', '=', wo.name)
        ])
        return payment_lines

    def terbilang(self, amount):
        hasil = fungsi_terbilang.terbilang(amount, "idr", 'id')
        return hasil

    def time_date(self):
        return datetime.now().strftime('%d-%m-%Y %H:%M')

    def print_user(self):
        return self.env['res.users'].suspend_security().browse(self.env.uid).name

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.work.order'].sudo().browse(docids)

        kwitansi_lines = {}
        for doc in docs:
            lines = self._get_kwitansi_lines(doc)
            if not lines:
                raise ValidationError(_('Cetak Kuitansi Belum Tersedia untuk WO: %s!') % doc.name)
            kwitansi_lines[doc.id] = lines

        return {
            'doc_ids': docids,
            'doc_model': 'tw.work.order',
            'docs': docs,
            'kwitansi_lines': kwitansi_lines,
            'terbilang': self.terbilang,
            'time_date': self.time_date,
            'print_user': self.print_user,
        }
