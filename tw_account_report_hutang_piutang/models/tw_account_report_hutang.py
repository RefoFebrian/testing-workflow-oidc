# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import pytz
import base64
import csv
import xlsxwriter
import calendar
from io import StringIO,BytesIO
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwAccountReportHutang(models.TransientModel):
    _name = "tw.account.report.hutang"
    _description = "Report Hutang (Payable Report)"

    def _get_default_date(self): 
        return datetime.now()
    
    name = fields.Char('File Name')
    date = fields.Date('Per Tanggal')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    trx_start_date = fields.Date('Trx Start Date')
    trx_end_date = fields.Date('Trx End Date', default=_get_default_date)
    status = fields.Selection([('outstanding','Outstanding'),('reconciled','Reconciled')], 'Status', default='outstanding')
    option = fields.Selection([('all','All Hutang'),('unit','Hutang Unit'),('other','Other Receivable')], string='Option', default='all')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')

    # 9: relation fields
    company_ids = fields.Many2many('res.company',string="Branch")
    partner_ids = fields.Many2many('res.partner',string='Partners')
    journal_ids = fields.Many2many('account.journal',string='Journals')
    account_ids = fields.Many2many('account.account',string='Accounts')

    def action_download(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self._get_detail_report()
    
    def _get_where_clause(self):
        query_where = "WHERE 1=1 AND am.state = 'posted' AND aml.credit > 0"

        if self.date:
            # TODO : di teds 1, date tidak berpengaruh ke filter AML, hanya residualnya saja, confirm ke accounting.
            # TODO : Karena, jika tidak di filter, saat ambil per tanggal 20, AML tanggal 21 akan tetap muncul, hanya saja pasti terbaca blm terbayar.
            rdate = self.date.strftime('%Y-%m-%d')
            query_where += f" AND aml.date <= '{rdate}'"

        if self.option == 'other':
            query_where += " AND tor.id IS NOT NULL"    
        else:
            query_where += " AND aa.account_type in ('liability_payable','liability_current') "
        
        if self.status == 'outstanding':
            query_where += " AND afr.id IS NULL"
        elif self.status == 'reconciled':
            query_where += " AND afr.id IS NOT NULL"
        
        if self.company_ids:
            query_where += f" AND aml.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND aml.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.journal_ids:
            query_where += f" AND am.journal_id IN ({', '.join(str(j.id) for j in self.journal_ids)})"
        
        if self.account_ids:
            query_where += f" AND aml.account_id IN ({', '.join(str(a.id) for a in self.account_ids)})"
        if self.partner_ids:
            query_where += f" AND aml.partner_id IN ({', '.join(str(p.id) for p in self.partner_ids)})"

        if self.trx_start_date:
            query_where += f" AND am.date >= '{self.trx_start_date.strftime('%Y-%m-%d')}'"
        if self.trx_end_date:
            query_where += f" AND am.date <= '{self.trx_end_date.strftime('%Y-%m-%d')}'"

        if self.start_date:
            query_where += f" AND aml.date_maturity >= '{self.start_date.strftime('%Y-%m-%d')}'"
        if self.end_date:
            query_where += f" AND aml.date_maturity <= '{self.end_date.strftime('%Y-%m-%d')}'"
        
        if self.division:
            query_where += f" AND am.division = '{self.division}'"
            
        return query_where

    def _get_detail_report(self, return_fp=False):
        if not (self.start_date and self.end_date) and not (self.trx_start_date and self.trx_end_date):
            raise Warning(_("Silahkan isi start date & end date untuk Tanggal JTP atau Transaction Date"))

        query_where = self._get_where_clause()
        
        cut_off_date = "current_date"
        if self.date:
            cut_off_date = f"'{self.date.strftime('%Y-%m-%d')}'"
        
        # Get summary header
        summary_header = self._get_summary_header_data()
        query = f"""
            SELECT 
                branch.code as branch
                , am.division as division 
                , rp.code as partner_code
                , rp.name as partner_name
                , aa.code_store->>'1' as account_code
                , COALESCE(LEFT(aa.code_store->>'1',6),'') || '-' || COALESCE(branch.profit_centre,'') || COALESCE(RIGHT(aa.sap,-6),'') as no_sun
                , am.name as no_sistem
                , aml.name as name
                , aml.ref as reference
                , am.invoice_origin as supplier_invoice_number
                , am.date as tanggal
                , od.overdue as "Tgl Jatuh Tempo"
                , case when afr.id is not null then 'Reconciled' else 'Outstanding' end as status
                , aml.amount_currency*-1 as total_invoice
                , residual.amount as sisa_hutang
                -- Aging bucket columns
			    ,CASE 
			        WHEN (od.overdue <= 0 OR aml.date_maturity IS NULL)
			        THEN residual.amount
					ELSE 0
			    END as current
			    ,CASE 
			        WHEN (od.overdue > 0 AND od.overdue < 8)
			        THEN residual.amount
					ELSE 0
			    END as overdue_1_7
			    ,CASE 
			        WHEN (od.overdue > 7 AND od.overdue < 15)
			        THEN residual.amount
					ELSE 0
			    END as overdue_8_14
			    ,CASE 
			        WHEN (od.overdue > 14 AND od.overdue < 22)
			        THEN residual.amount
					ELSE 0
			    END as overdue_15_21
			    ,CASE 
			        WHEN (od.overdue > 21 AND od.overdue < 31)
			        THEN residual.amount
					ELSE 0
			    END as overdue_22_30
			    ,CASE 
			        WHEN (od.overdue > 30 AND od.overdue < 61)
			        THEN residual.amount
					ELSE 0
			    END as overdue_31_60
			    ,CASE 
			        WHEN (od.overdue > 60 AND od.overdue < 91)
			        THEN residual.amount
					ELSE 0
			    END as overdue_61_90
			    ,CASE 
			        WHEN (od.overdue > 90)
			        THEN residual.amount
					ELSE 0
			    END as overdue_91_n
                -- End of Aging bucket columns
			    , aml.ref as reference
			    , aj.name->>branch_partner.lang as src
			    , rup.name as create_by
			    , rucp.name as confirm_by
            FROM account_move_line aml
            LEFT JOIN account_move am ON am.id = aml.move_id 
            LEFT JOIN tw_account_period ap ON ap.id = am.period_id 
            LEFT JOIN account_account aa ON aa.id = aml.account_id 
            LEFT JOIN res_company branch ON branch.id = am.company_id
            LEFT JOIN res_partner branch_partner ON branch_partner.id = branch.partner_id  
            LEFT JOIN account_journal aj ON aj.id = am.journal_id 
            LEFT JOIN LATERAL (
            	SELECT aml.id,max(full_reconcile_id) as full_reconcile_id, sum(amount) as amount
            	FROM account_partial_reconcile apr
            	where (apr.debit_move_id = aml.id or apr.credit_move_id = aml.id)
                AND (apr.create_date + interval '7 hours')::date <= {cut_off_date}
                GROUP BY aml.id
            ) as reconcile on reconcile.id = aml.id 
            LEFT JOIN LATERAL (SELECT aml.id,(aml.amount_currency*-1) - COALESCE(reconcile.amount,0) as amount) as residual on residual.id = aml.id
            LEFT JOIN account_full_reconcile afr ON afr.id = reconcile.full_reconcile_id 
            LEFT JOIN res_partner rp ON rp.id = aml.partner_id 
            LEFT JOIN LATERAL (SELECT aml.id,{cut_off_date} - aml.date_maturity as overdue) as od on od.id = aml.id
            LEFT JOIN tw_other_receivable tor on tor.move_id = am.id
            LEFT JOIN res_users ru on ru.id = COALESCE(tor.create_uid,am.create_uid)
            LEFT JOIN res_partner rup on rup.id = ru.partner_id
            LEFT JOIN res_users ruc on ruc.id = COALESCE(tor.confirm_uid,am.confirm_uid)
            LEFT JOIN res_partner rucp on rucp.id = ruc.partner_id
            {query_where}
        """
        
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        
        return self.env['web.report'].sudo().generate_report('Report Hutang ',ress, data_summary_header=summary_header,data_summary_header_col_size=False, return_fp=return_fp)
    
    def _get_summary_header_data(self):
        tanggal = self.date.strftime('%Y-%m-%d') if self.date else self._get_default_date().strftime('%Y-%m-%d')
        return {
            "A1": self.env.user.company_id.parent_id.name or self.env.user.company_id.name,
            "A2": "Laporan Hutang Per Tanggal %s" % tanggal,
            "A3": "Tanggal Jatuh Tempo : %s s/d %s" % (self.start_date.strftime('%Y-%m-%d') if self.start_date else '-', self.end_date.strftime('%Y-%m-%d') if self.end_date else '-'),
            "A4": "Tanggal Transaksi : %s s/d %s" % (self.trx_start_date.strftime('%Y-%m-%d') if self.trx_start_date else '-', self.trx_end_date.strftime('%Y-%m-%d') if self.trx_end_date else '-'),
        }