# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields
from odoo.exceptions import UserError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwServicePackage(models.Model):
    _name = "tw.service.package"
    _description = "Master Paket Service"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Nama', required=True)
    date = fields.Date(string='Tanggal', default=fields.Date.context_today)
    active = fields.Boolean(string='Aktif', default=True)
    is_priority = fields.Boolean(string='Prioritas')

    # 9: relation fields
    line_ids = fields.One2many('tw.service.package.line', 'package_id', string='Detail Paket', context={'active_test': False})
    company_id = fields.Many2one('res.company', string='Branch', required=True)
    area_id = fields.Many2one('res.area', string='Area', help="Isi apabila paket ini dikhususkan untuk area tertentu. Kosongkan jika berlaku untuk semua area di branch ini.")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def unlink(self):
        work_order = self.env['tw.work.order']
        for package in self:
            wo_using_package = work_order.search(['|',('service_package_ids', 'in', package.id),('service_package_priority_ids', 'in', package.id),])

            if wo_using_package:
                wo_names = ', '.join(wo_using_package.mapped('name'))
                raise UserError(f"Tidak dapat menghapus '{package.name}' karena sudah digunakan di Work Order: {wo_names}")

        return super(TwServicePackage, self).unlink()

    # 13: action methods

    # 14: private methods