from odoo import models, fields, api

class TWReportPembelianPartAhm(models.TransientModel):
    _inherit = "tw.report.pembelian.part.ahm"

    def generate_pembelian_part_ahm_report(self, kwargs):
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        
        report = self.create({
            'start_date': start_date,
            'end_date': end_date,
        })

        return report.generate_report(return_fp=True)
        