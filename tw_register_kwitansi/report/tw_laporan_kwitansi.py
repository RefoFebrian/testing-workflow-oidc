# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import pytz
# 6: Import of unknown third party lib
class TWLaporanKwitansi(models.TransientModel):
    _name = "tw.laporan.kwitansi.wizard"
    _description = "Report Laporan Kwitansi"

    STATE_SELECTION =[
        ('open','Open'),
        ('printed','Printed'),
        ('cancel','Canceled'),
    ]

    start_date = fields.Date(string="Start Date", default=lambda self: datetime.today().date())
    end_date = fields.Date(string="End Date", default=lambda self:datetime.today().date())
    state = fields.Selection(STATE_SELECTION, string="State")
    # company_ids = fields.Many2many(
    #     'res.company',
    #     'tw_laporan_kwitansi_relation',
    #     'laporan_kwitansi_wizard_id',
    #     'branch_id',
    #     string="Branches",
    #     help="Select branches to include in the report.",
    #     default=lambda self: self.env.user.company_ids.ids
    # )
    company_ids = fields.Many2many(
                    'res.company',
                    string='Companies',
                    default= lambda self: self.env.user.company_ids.ids
                )

    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        self.ensure_one()

        start_date = self.start_date
        end_date = self.end_date
        state = self.state

        if start_date and end_date and start_date > end_date:
            raise Warning("Silahkan masukkan rentang tanggal yang valid.")

        company_ids = self.company_ids
        summary_header = {
            'A1': self.env.user.company_id.name,
            'A2': 'Report Kwitansi '+str(self.get_local_time()),
            'A3': 'Tanggal : '+str(start_date)+' s/d '+str(end_date)
        }
        
        query_where = f"WHERE 1=1"
        
        if start_date:
            query_where += f" AND rk.date >= '{start_date}'"
        if end_date:
            query_where += f" AND rk.date <= '{end_date}'"
        if state:
            query_where += f" AND rkl.state = '{state}'"
        

        if company_ids:
            query_where += f" AND rk.company_id IN {str(tuple([b.id for b in self.company_ids])).replace(',)', ')')}"

        query = f"""
            select 
                b.code as branch_code
                , rkl.name as no_kwitansi
                , ap.name as no_transaksi
                , rp.name AS partner
                , ap.memo as keterangan
                , rk.date as tanggal
                , am.number_faktur_pajak
                , rkl.reason as reason
            from tw_register_kwitansi rk
            LEFT join tw_register_kwitansi_line rkl on rk.id = rkl.register_kwitansi_id 
            LEFT join res_company b on b.id = rk.company_id 
            LEFT join tw_account_payment ap on ap.id = rkl.payment_id
            LEFT join account_move am on am.id = ap.move_id
            LEFT join res_partner rp on rp.id = ap.partner_id 
            {query_where}
        """

        self._cr.execute(query)
        ress =  self._cr.dictfetchall()

        if not ress:
            raise Warning("Tidak ada data untuk periode dan cabang yang dipilih")
        
        report_action = self.env['web.report'].sudo().generate_report('Laporan Kwitansi', ress,data_summary_header=summary_header,show_total_footer=False)
        report_action['close_on_report_download'] = True
        return report_action

    def get_local_time(self):
        user = self.env.user
        now_utc = datetime.now(pytz.utc)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now_local = now_utc.astimezone(tz)
        return now_local.strftime("%d-%m-%Y %H:%M")
    
    