# 1: imports of python lib
from datetime import date, datetime, timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class EmployeeMekanikMitra(models.Model):
    _inherit = "hr.employee"

    # 7: defaults methods

    # 8: fields
    agreement_to = fields.Char('Perjanjian Ke')
    start_date = fields.Date('Tanggal Mulai')
    end_date = fields.Date('Tanggal Selesai')
    description = fields.Text('Keterangan')
    agreement_letter = fields.Selection([
        ('Belum','Belum'),
        ('Proses','Proses'),
        ('OK','OK')])
    absen_finger = fields.Char('Absensi Finger ID')

    @api.model_create_multi
    def create(self, vals_list):
        res =  super(EmployeeMekanikMitra, self).create(vals_list)
        mitra_obj = self.env['hr.employee.category'].search([('name','=','Mitra')],limit=1)
        job_obj = self.env['hr.job'].search([('sales_force_id.value','=','mechanic')],limit=1)
        for hr in res:
            if hr.agreement_to:
                if not mitra_obj:
                    raise Warning(_('Kategori Mitra tidak ditemukan!'))
                if not job_obj:
                    raise Warning(_('Job Mekanik tidak ditemukan!'))
                hr.category_ids = [(4, mitra_obj.id)]
                hr.job_id = job_obj.id
        return res