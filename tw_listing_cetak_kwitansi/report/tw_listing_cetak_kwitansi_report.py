# 1: imports of python lib
from datetime import datetime, date, timedelta
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwListingCetakKwitansiReport(models.TransientModel):
    _name = "tw.listing.cetak.kwitansi.report"
    _description = 'Report Listing Cetak Kwitansi'

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    wbf = {}

    # 8: fields
    name = fields.Char(string='Filename')
    state_x = fields.Selection((
        ('choose', 'choose'),
        ('get', 'get')
    ), default=lambda *a: 'choose', string='State')
    start_date = fields.Date(string='Start Date', default=_get_default_date)
    end_date = fields.Date(string='End Date', default=_get_default_date)
    data_x = fields.Binary(string='File', readonly=True)

    # 9: relation fields
    company_ids = fields.Many2many('res.company', 'tw_listing_cetak_kwitansi_report_company_rel', 'tw_listing_cetak_kwitansi_report_id', 'company_id', "Branch", copy=False, domain=[('parent_id','!=',False)])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_listing_cetak_kwitansi_report_tree(self):
        domain = []
        name = 'Laporan Listing Cetak Kwitansi'
        path = 'laporan-listing-cetak-kwitansi'
        form_view_id = self.env.ref('tw_listing_cetak_kwitansi.tw_listing_cetak_kwitansi_report_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.listing.cetak.kwitansi.report',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_export(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        ress = self._get_listing_cetak_kwitansi_report_data()
        if not ress:
            raise Warning(f'Data Listing Cetak Kwitansi tidak ada !')

        return self.env['web.report'].sudo().generate_report('Laporan Listing Cetak Kwitansi', ress)

    # 14: private methods
    def _get_listing_cetak_kwitansi_report_data(self):
        query_where = " WHERE lck.state != 'draft'"
        if self.start_date:
            query_where += f" AND lck.date >= '{self.start_date}'"
        if self.end_date:
            query_where += f" AND lck.date <= '{self.end_date}'"

        if self.company_ids:
            query_where += f" AND lck.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            companies = self.env.user._get_company_ids()
            query_where += f" AND lck.company_id IN {str(tuple(companies)).replace(',)', ')')}"

        query = f"""
            SELECT
                lck.name AS no_kwitansi
                , lck.date AS tanggal_kwitansi
                , b.code AS kode_cabang
                , b.name AS nama_cabang
                , lck.payer_name
                , lck.editorial
                , lck.total AS jumlah
                , j.name ->> 'en_US' AS no_rekening
                , lck.account_name
                , lck.number_faktur_pajak
                , lck.reference_no
                , lck.proof_of_payment_no
                , lck.payment_date
                , lck.transaction_type
                , lck.state
            FROM tw_listing_cetak_kwitansi lck
            INNER JOIN res_company b ON b.id = lck.company_id
            INNER JOIN account_journal j ON j.id = lck.journal_id
            {query_where}
            ORDER BY lck.name ASC
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        return ress
    