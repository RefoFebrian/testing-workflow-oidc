from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import timedelta

class TWReportFakturPajak(models.TransientModel):
    _name = "tw.report.faktur.pajak"
    _description = "TW Report Payment"

    def _get_allowed_company_ids(self):
        """Get company IDs to filter. Use selected or fallback to user's companies."""
        if self.company_ids:
            return self.company_ids.ids
        return self.env.user.company_ids.ids

    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
    
    option = fields.Selection([
        ('faktur_pajak','Faktur Pajak'),
        ('generate_faktur_pajak','Generate Faktur Pajak'),
        ('faktur_pajak_gabungan','Faktur Pajak Gabungan'),
        ('faktur_pajak_others','Faktur Pajak Others'),
    ], string='Option', default='faktur_pajak',required=True)
    
    pajak_gabungan = fields.Boolean(string='Pajak Gabungan')
    thn_penggunaan = fields.Char(string='Tahun Penggunaan')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    state_faktur_pajak = fields.Selection([
        ('open', 'Open'),
        ('close', 'Closed'),
        ('print', 'Printed'),
        ('cancel', 'Canceled'),
    ], string='State Faktur Pajak')

    state_generate_faktur_pajak = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], string='State Generate Faktur Pajak')

    state_other_faktur_pajak = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], string='State Other Faktur Pajak')

    state_gabungan_faktur_pajak = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='State Gabungan Faktur Pajak')

    company_ids = fields.Many2many("res.company", string="Branch", domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    partner_ids = fields.Many2many("res.partner", string="Partner", domain=lambda self: [('company_id', 'in', self.env.user.company_ids.ids)])
    model_ids = fields.Many2many("ir.model", string="Form")
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options_list(['Unit','Sparepart','Umum']), string='Division', default='Unit')

    @api.constrains('thn_penggunaan')
    def _check_thn_penggunaan(self):
        for rec in self:
            if rec.thn_penggunaan and (len(rec.thn_penggunaan) != 4 or not rec.thn_penggunaan.isdigit()):
                raise Warning("Tahun Penggunaan harus 4 digit angka.")

    def action_generate_report(self):
        if not self.env.user.has_group('tw_base.group_admin_report') and self.start_date and self.end_date:
            self.check_date_range_limit(self.start_date, self.end_date)
        
        if self.option == 'faktur_pajak':
            ress = self._print_excel_report_faktur_pajak()
            report_name = f"Laporan Faktur Pajak"
        elif self.option == 'generate_faktur_pajak':
            ress, ress_2 = self._print_excel_report_generate_faktur_pajak()
            report_name = f"Laporan Generate Faktur Pajak"

            data_sheet = {'Laporan Faktur Pajak': ress, 'Laporan Faktur Pajak Detail': ress_2}
            return self.env['web.report'].sudo().generate_report(report_name, data=ress,data_sheet=data_sheet,show_total_footer=True,freeze_panes_column=3,start_date=self.start_date,end_date=self.end_date)
        elif self.option == 'faktur_pajak_gabungan':
            ress = self._print_excel_report_faktur_pajak_gabungan()
            report_name = f"Laporan Faktur Pajak Gabungan"
        elif self.option == 'faktur_pajak_others':
            ress = self._print_excel_report_faktur_pajak_others()
            report_name = f"Laporan Faktur Pajak Others"
        
        return self.env['web.report'].sudo().generate_report(report_name, ress,show_total_footer=True,freeze_panes_column=3,start_date=self.start_date,end_date=self.end_date)
    
    
    def check_date_range_limit(self, start_date, end_date):
        limit = int(self.env['ir.config_parameter'].sudo().get_param('tw_base.report_date_range_limit',30))
        if end_date - start_date > timedelta(limit):
            raise Warning('Perhatian!\nRange tanggal tidak lebih dari 30 hari.')

    def _print_excel_report_faktur_pajak(self):
        query_where = "WHERE 1=1"
        allowed_companies = self._get_allowed_company_ids()

        if self.start_date:
            query_where += " AND fpo.date >= '%s'" % self.start_date
        if self.end_date:
            query_where += " AND fpo.date <= '%s'" % self.end_date
        if self.pajak_gabungan:
            query_where += " AND fpg.id is not null"
        if self.state_faktur_pajak:
            query_where += " AND fpo.state = '%s'" % self.state_faktur_pajak
        if self.thn_penggunaan:
            query_where += " AND EXTRACT(YEAR FROM fpo.date)= %s" % self.thn_penggunaan
        if self.model_ids:
            query_where += " AND m.id in %s" % str(tuple(self.model_ids.ids)).replace(',)', ')')
        if self.partner_ids:
            query_where += " AND p.id in %s" % str(tuple(self.partner_ids.ids)).replace(',)', ')')
        if allowed_companies:
            company_filter = str(tuple(allowed_companies)).replace(',)', ')')
            query_where += " AND fpo.company_id in %s" % company_filter

        query = """
            SELECT 
                fpo.name AS code_pajak,
                COALESCE(m.name->>'id_ID', m.name->>'en_US', '') AS form_name,
                CAST(fpg.id IS NOT NULL AS Text) AS pajak_gabungan,
                p.code AS partner_code,
                fpo.date::Text AS tanggal_transaksi,
                fpo.release_date::Text  AS tanggal_terbit, 
                CAST(EXTRACT(YEAR FROM fpo.date) AS Text) AS tahun,
                fpo.printed_count AS cetak_ke, 
                fpo.state AS state,
                fpo.untaxed_amount AS untaxed_amount,
                fpo.tax_amount AS tax_amount,
                fpo.amount_total AS amount_total
            FROM tw_faktur_pajak_out fpo 
                LEFT JOIN ir_model m ON m.id = fpo.model_id
                LEFT JOIN tw_faktur_pajak_gabungan fpg ON fpg.faktur_pajak_out_id = fpo.id
                LEFT JOIN res_partner p ON p.id = fpo.partner_id
            %s
            ORDER BY fpo.name , fpo.id
        """ % query_where
        
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        if not ress:
            raise Warning('Data tidak ada...')

        return ress