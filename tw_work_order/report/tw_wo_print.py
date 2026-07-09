# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class PrintWorkOrder(models.AbstractModel):
    _name = "report.tw_work_order.print_wo"
    _description = "Work Order Print WO"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_service_lines(self, order_line):
        no = 0
        lines = []
        for line in order_line:
            if line.division == 'Service':
                no += 1
                lines.append((no, line))
        return lines

    def _get_sparepart_lines(self, order_line):
        no = 0
        lines = []
        for line in order_line:
            if line.division == 'Sparepart':
                no += 1
                lines.append((no, line))
        return lines

    def time_date(self):
        return datetime.now().strftime('%d-%m-%Y %H:%M')

    def print_user(self):
        return self.env['res.users'].suspend_security().browse(self.env.uid).name

    def invoice_name(self):
        wo_obj = self.env['tw.work.order'].suspend_security().browse(
            self.env.context.get('active_ids', [])
        )
        move_obj = self.env['account.move'].suspend_security().search([
            ('ref', 'ilike', wo_obj.name),
            ('move_type', '=', 'out_invoice')
        ], limit=1)
        return move_obj.name if move_obj else '-'

    def estimasi_waktu(self, wo):
        estimasi = ''
        if hasattr(wo, 'start_date') and hasattr(wo, 'finish_date') and wo.start_date and wo.finish_date:
            diff = wo.finish_date - wo.start_date
            total_seconds = diff.total_seconds()
            selisih_menit = int(total_seconds // 60)
            selisih_detik = int(total_seconds % 60)
            estimasi = '%s Menit %s Detik' % (selisih_menit, selisih_detik)
        return estimasi

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.work.order'].sudo().browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'tw.work.order',
            'docs': docs,
            'get_service_lines': self._get_service_lines,
            'get_sparepart_lines': self._get_sparepart_lines,
            'time_date': self.time_date,
            'print_user': self.print_user,
            'invoice_name': self.invoice_name,
            'estimasi_waktu': self.estimasi_waktu,
        }
