# 1: imports of python lib
import datetime
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api


# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwStockOpnameBaksoDG(models.TransientModel):
    _name = "tw.stock.opname.bakso.dg"
    _description = "TW Stock Opname Bakso DG"

    # 7: defaults methods

    # 8: fields
    note_bakso = fields.Text('Note')

    # 9: relation fields
    opname_id = fields.Many2one('tw.stock.opname.direct.gift', 'Stock Opname')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_submit_bakso(self):
        active_ids = self.env.context.get('active_ids', [])

        tot_qty = 0
        tot_amount = 0
        tot_qty_fisik_baik = 0
        tot_qty_fisik_rusak = 0
        tot_amount_total = 0
        tot_selisih_qty = 0
        tot_selisih_amount = 0
        tot_saldo_log_book = 0
        tot_qty_fisik_baik_other = 0
        tot_qty_fisik_rusak_other = 0

        tot_qty_fisik_total = 0
        tot_dg_other = 0

        for line in self.opname_id.detail_ids:
            tot_qty += line.qty
            tot_amount += line.amount
            tot_qty_fisik_baik += line.qty_physical_good
            tot_qty_fisik_rusak += line.qty_physical_broken
            tot_qty_fisik_total += line.qty_physical_total
            tot_amount_total += line.amount_total
            tot_selisih_qty += line.diff_qty
            tot_selisih_amount += line.diff_amount
            tot_saldo_log_book += line.balance_log_book

        for other in self.opname_id.other_dg_ids:
            tot_saldo_log_book += other.balance_log_book
            tot_qty_fisik_baik_other += other.qty_physical_good
            tot_qty_fisik_rusak_other += other.qty_physical_broken
            tot_dg_other += other.qty_physical_total

        tot_dg = tot_qty_fisik_total + tot_dg_other

        datas = {
            'ids': active_ids,
            'name': str(self.opname_id.name),
            'branch': f"[{self.opname_id.company_id.code}] {self.opname_id.company_id.name}" if self.opname_id.company_id else '',
            'division': self.opname_id.division,
            'tgl_so': self.opname_id.date,
            'jam_mulai': (self.opname_id.generate_date + relativedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'jam_selesai': (self.opname_id.post_date + relativedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'note_bakso': str(self.note_bakso) if self.note_bakso else '',
            'pdi': self.opname_id.pdi_id.name or '',
            'adh': self.opname_id.adh_id.name or '',
            'soh': self.opname_id.soh_id.name or '',
            'user_id': {'name': self.env.user.name},
            'date': (datetime.datetime.now() + datetime.timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'tot_qty': tot_qty,
            'tot_amount': tot_amount,
            'tot_qty_fisik_baik': tot_qty_fisik_baik,
            'tot_qty_fisik_rusak': tot_qty_fisik_rusak,
            'tot_amount_total': tot_amount_total,
            'tot_selisih_qty': tot_selisih_qty,
            'tot_selisih_amount': tot_selisih_amount,
            'tot_saldo_log_book': tot_saldo_log_book,
            'tot_qty_fisik_baik_other': tot_qty_fisik_baik_other,
            'tot_qty_fisik_rusak_other': tot_qty_fisik_rusak_other,
            'tot_qty_fisik_total': tot_qty_fisik_total,
            'tot_dg_other': tot_dg_other,
            'tot_dg': tot_dg,

        }
        self.opname_id.suspend_security().note_bakso = self.note_bakso
        return self.env.ref('tw_stock_opname_direct_gift.action_tw_so_dg_print_bakso').report_action(self, data=datas)

    # 14: private methods