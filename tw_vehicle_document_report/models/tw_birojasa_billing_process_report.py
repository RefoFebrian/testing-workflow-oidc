from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning

class BirojasaBillingProcessReport(models.TransientModel):
    _name = "tw.birojasa.billing.process.report"
    _description = "Birojasa Billing Process Report"

    def _get_default_date(self): 
        return datetime.now()

    def _get_default_companies(self):
        return self.env.company.ids
    
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)

    company_ids = fields.Many2many(
        comodel_name='res.company', 
        relation='tw_birojasa_billing_process_report_company_rel',
        column1='birojasa_billing_process_report_id', 
        column2='company_id',
        string='Branch',
        default=_get_default_companies,
        domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)]
    )
    biro_jasa_id = fields.Many2one(comodel_name='res.partner', domain=[('category_id.name', '=', 'Birojasa')])
    state = fields.Selection([
        ('all', 'All'),
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='all')

    def _get_allowed_company_ids(self):
        """Get company IDs to filter. Use selected or fallback to user's companies."""
        if self.company_ids:
            return self.company_ids.ids
        return self.env.user.company_ids.ids

    def action_export_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        
        # Always filter by allowed companies
        allowed_companies = self._get_allowed_company_ids()
        company_filter = str(tuple(allowed_companies)).replace(',)', ')')
        where = f" AND b.id in {company_filter}"
        
        if self.start_date:
            where += " AND pb.date >= '%s' " % (self.start_date)
        if self.end_date:
            where += " AND pb.date <= '%s' " % (self.end_date)
        if self.biro_jasa_id:
            where += " AND rp.id = %s "  % (self.biro_jasa_id.id)
        if self.state and self.state != 'all':
            where += " AND pb.state = '%s' " % (self.state)

        query = f"""
            select 
                b.code kode_branch, 
                b.name nama_branch, 
                pb.name "No PRBJ", 
                pb.date "Tanggal PRBJ", 
                pb.state "Status PRBJ", 
                rp.code "Kode Birojasa", 
                rp.name "Nama Birojasa", 
                pb.type "Type", 
                pb.document_number "No Tagihan", 
                pb.description "Deskripsi", 
                lot.name "No Mesin", 
                lot.chassis_number "No Rangka", 
                cust.code "Kode Pemilik STNK", 
                cust.name "Nama Pemilik STNK", 
                pbl.notice_number "No Notice", 
                pbl.notice_date "Tanggal Notice", 
                pbl.estimation_amount "Estimasi Tagihan", 
                pbl.progressive_tax_amount "PPN", 
                pbl.amount_total "Total Tagihan", 
                pbl.correction_amount "Koreksi Tagihan", 
                payment.payment_number "No Pembayaran", 
                payment.payment_state "Status Pembayaran",
                payment.invoice_number "No Invoice"
            from tw_birojasa_billing_process pb 
            LEFT join tw_birojasa_billing_process_line pbl on pb.id = pbl.birojasa_billing_id
            left join res_company b on pb.company_id = b.id 
            left join res_partner rp on pb.biro_jasa_id = rp.id 
            left join stock_lot lot on pbl.lot_id = lot.id 
            left join res_partner cust on lot.customer_stnk_id = cust.id 
            left join lateral(
                select 
                    array_to_string(array_agg(distinct wav.name), ', ') as payment_number,
                    array_to_string(array_agg(distinct ai.name), ', ') as invoice_number,
                    string_agg(distinct ai.state, ', ') as payment_state
                from tw_account_payment wav
                inner join tw_account_payment_line wavl on wav.id = wavl.payment_id
                inner join account_move_line aml on wavl.move_line_id = aml.id
                left join account_move ai on ai.id = aml.move_id
                where wavl.type = 'dr' 
                and ai.ref = pb.name
            ) payment on true
            where 1=1
            {where}
            order by pb.date, pb.id 
            """
    
        self._cr.execute(query)
        ress = self._cr.dictfetchall()

        return self.env['web.report'].sudo().generate_report(
            'Laporan PRBJ',
            ress,
            start_date=self.start_date,
            end_date=self.end_date,
            header_title=False
        )
