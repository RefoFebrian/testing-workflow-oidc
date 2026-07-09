# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrder(models.Model):
    _inherit = "tw.work.order"
    # 7: defaults methods

    # 8: fields
    state_lcr = fields.Selection([
        ('draft', 'Draft'),
        ('outstanding', 'Outstanding'),
        ('done', 'Done')
    ], string='State PUD')
    consumer_willingness = fields.Selection([
        ('01', 'Bersedia Langsung Dilakukan Pengecekan/Pengerjaan'),
        ('02', 'Bersedia Dicek Di Lain Waktu'),
        ('03', 'Tidak Bersedia')
    ], string='Kesediaan LCR')
    check_results = fields.Selection([
        ('01', 'Butuh Dilakukan Treatment'),
        ('02', 'Butuh Dilakukan Penggantian')
    ], string='Hasil Pengecekan LCR')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def _prepare_rfa(self,obj_po):
        # Validasi LCR
        if obj_po.state_lcr in ('draft', 'outstanding') and obj_po.consumer_willingness == '01':
            msg = ''
            if 'Treatment' in obj_po.notification:
                master_lcr_id = self.env['tw.selection'].search([
                    ('value', 'in', ['LCR Treatment', 'LCR Treatment 2']),
                    ('type', '=', 'LCRNotification')
                ])
                msg = 'Treatment/Treatment 2'
            elif 'Penggantian' in obj_po.notification:
                master_lcr_id = self.env['tw.selection'].search([
                    ('value', '=', 'LCR Penggantian'),
                    ('type', '=', 'LCRNotification')
                ])
                msg = 'Penggantian'
            else:
                master_lcr_id = self.env['tw.selection'].search([
                    ('value', '=', 'LCR Check'),
                    ('type', '=', 'LCRNotification')
                ])
                msg = 'Pengecekan'

            if not master_lcr_id:
                raise ValidationError("Mohon buat Master LCR pada TW Selection dengan type LCR (ex. LCR Check)")

            is_any_lcr = False
            if not obj_po.work_order_line_ids:
                raise ValidationError("Kendaraan terdeteksi pada Master LCR. Mohon masukkan Service terlebih dahulu.")
            for line in obj_po.work_order_line_ids:
                if any(line.product_id.name.lower() in value.lower() for value in master_lcr_id.mapped('value')):
                    is_any_lcr = True
                    break
            if not is_any_lcr:
                raise ValidationError(f"Kendaraan terdeteksi pada Master LCR. Mohon masukkan Service dengan Produk LCR {msg}")
        prepare = super()._prepare_rfa(obj_po)
        return prepare