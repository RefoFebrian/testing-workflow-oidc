# 1: imports of python lib
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, api, fields, _


# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwVehicleDocumentBaksoOwnership(models.TransientModel):
    _name = "tw.vehicle.document.bakso.ownership"
    _description = "Vehicle Document Bakso Ownership"

    # 7: defaults methods

    # 8: fields
    note_bakso = fields.Text('Note')

    # 9: relation fields
    opname_id = fields.Many2one('tw.vehicle.document.stock.opname', 'Stock Opname')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_submit_bakso(self):
        active_ids = self.env.context.get('active_ids', [])

        saldo_sistem = len(self.opname_id.detail_bpkb_ids)
        saldo_cabang = 0
        saldo_ho = 0
        saldo_ga = 0
        saldo_md = 0
        saldo_birojasa = 0
        saldo_konsumen = 0
        saldo_leasing = 0
        saldo_lainnya = 0
        other_bpkb = len(self.opname_id.other_bpkb_ids)

        for line in self.opname_id.detail_bpkb_ids:
            if line.validation_check_physical_ownership == 'Fisik Ada':
                saldo_cabang += 1
            elif line.validation_check_physical_ownership == 'Fisik di HO':
                saldo_ho += 1
            elif line.validation_check_physical_ownership == 'Fisik di GA':
                saldo_ga += 1
            elif line.validation_check_physical_ownership == 'Fisik di MD':
                saldo_md += 1
            elif line.validation_check_physical_ownership == 'Revisi Biro Jasa':
                saldo_birojasa += 1
            elif line.validation_check_physical_ownership == 'Sudah Penyerahan ke Konsumen':
                saldo_konsumen += 1
            elif line.validation_check_physical_ownership == 'Sudah Penyerahan ke Leasing':
                saldo_leasing += 1
            elif line.validation_check_physical_ownership == 'Hilang / Fisik tidak diketahui':
                saldo_lainnya += 1

        selisih_sistem_fisik = saldo_sistem - saldo_cabang - saldo_ho - saldo_ga - saldo_md - saldo_birojasa - saldo_konsumen - saldo_leasing - saldo_lainnya
        total_stock = saldo_cabang + other_bpkb
        datas = {
            'ids': active_ids,
            'name': str(self.opname_id.name),
            'branch': str(self.opname_id.company_id.display_name),
            'division': self.opname_id.division,
            'tgl_so': self.opname_id.date,
            'jam_mulai': (self.opname_id.generate_date + relativedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'jam_selesai': (self.opname_id.post_date + relativedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'saldo_sistem': saldo_sistem,
            'saldo_cabang': saldo_cabang,
            'saldo_ho': saldo_ho,
            'saldo_ga': saldo_ga,
            'saldo_md': saldo_md,
            'saldo_birojasa': saldo_birojasa,
            'saldo_konsumen': saldo_konsumen,
            'saldo_leasing': saldo_leasing,
            'saldo_lainnya': saldo_lainnya,
            'selisih_sistem_fisik': selisih_sistem_fisik,
            'other_bpkb': other_bpkb,
            'total_stock': total_stock,
            'note_bakso': str(self.note_bakso) if self.note_bakso else '',
            'staff_bbn_id': self.opname_id.staff_bbn_id.name,
            'adh_id': self.opname_id.adh_id.name,
            'soh_id': self.opname_id.soh_id.name,
            'printed_user': self.env.user.name,
            'date': (datetime.now() + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
        }
        self.opname_id.note_bakso = self.note_bakso

        return self.env.ref('tw_vehicle_document_stock_opname.action_report_bakso_bpkb').report_action(self, data=datas)

    # 14: private methods
