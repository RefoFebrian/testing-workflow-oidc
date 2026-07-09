# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import datetime, timedelta

class TWDetailFakturPajakMasukan(models.TransientModel):
    _name = "tw.detail.faktur.pajak.masukan"
    _description = "TW Detail Faktur Pajak Masukan"

    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    name = fields.Char(string="Filename", readonly=True)
    file = fields.Binary(string="File", readonly=True)
    start_date = fields.Date(string="Start Date",required=True)
    end_date = fields.Date(string="End Date",required=True)
    company_id = fields.Many2one("res.company", string="Branch")
    partner_id = fields.Many2one("res.partner", string="Supplier")

    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = ""
        if self.company_id:
            query_where += " AND tpr.company_id = %d" % self.company_id.id
        if self.start_date and self.end_date:
            query_where += " AND tpr.date_faktur_pajak  BETWEEN '%s' AND '%s'" % (str(self.start_date), str(self.end_date))
        if self.partner_id:
            query_where += " AND tpr.partner_id = %d" % self.partner_id.id

        summary_header = self._get_summary_header_data()
        query = """
             SELECT DISTINCT
                partner.name AS nama_vendor
                , tpr.memo AS memo
                , tpr.number_faktur_pajak AS no_faktur_pajak
                , tpr.date_faktur_pajak AS tanggal_faktur_pajak
                , coalesce(Round(tprl.amount / coalesce((coalesce(tax.amount +100)/100),1),2)) AS dpp
                , coalesce(Round(tprl.amount - (tprl.amount / coalesce((coalesce(tax.amount +100)/100),1)),2)) AS ppn
                , av.name AS payment_number
                , av.date AS payment_date
                , av.amount AS payment_amount
                , tpr.name AS reference
                , tpr.document_number  AS invoice_number
                , tpr.document_date AS invoice_date
            FROM tw_payment_request tpr
            LEFT JOIN tw_payment_request_line tprl on tprl.payment_id = tpr.id and tpr.name LIKE 'NC%%'
            LEFT JOIN account_tax_tw_payment_request_line_rel tax_rel on tax_rel.tw_payment_request_line_id = tprl.id 
            LEFT JOIN account_tax tax
		       ON tax.id = COALESCE(
		            tax_rel.account_tax_id
	       	)
            LEFT JOIN res_partner partner ON tpr.partner_id = partner.id
            LEFT JOIN account_move am ON tpr.move_id = am.id
            LEFT JOIN account_move_line aml ON aml.move_id = am.id
            LEFT JOIN tw_account_payment_line avl ON avl.move_line_id = aml.id
            LEFT JOIN tw_account_payment av ON avl.payment_id = av.id
            WHERE 1=1
            AND tpr.date_faktur_pajak IS NOT NULL
            AND tpr.state = 'paid'
            AND am.state = 'posted'
            AND aml.credit > 0
            %s
        """ % (query_where)

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        if not ress:
            raise Warning('Data tidak ada...')
        report_name = f"Laporan Detail Faktur Pajak Masukan"
        return self.env['web.report'].sudo().generate_report(report_name, ress,show_total_footer=False,data_summary_header=summary_header,data_summary_header_col_size=False, freeze_panes_column=3)
        
    def _get_summary_header_data(self):
        company_name = self.company_id.name
        return {
            "A3": company_name if self.company_id else '-',
            "A4": "Detail Faktur Pajak Masukan Periode : %s s/d %s" % (self.start_date if self.start_date else '-', self.end_date if self.end_date else '-'),
        }
    