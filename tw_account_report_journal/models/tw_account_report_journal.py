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
from datetime import date, datetime, time,timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwAccountReportJournal(models.TransientModel):
    _name = "tw.account.report.journal"
    _description = "Report Journal"

    def _get_default_date(self): 
        return datetime.now()
    
    name = fields.Char('File Name')
    start_date = fields.Date('Start Date', default=lambda self: self._get_default_date().replace(day=1))
    end_date = fields.Date('End Date', default=_get_default_date)
    option = fields.Selection([
        ('detail', 'Detail per account'),
        #? Report summary belum ada di existing. Jika mau di buat harus di confirm dulu
        # ('summary', 'Summary per account'),
    ], string='Option', default='detail')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    # 9: relation fields
    period_id = fields.Many2one('tw.account.period', 'Period')
    company_ids = fields.Many2many('res.company',string="Branch")
    journal_ids = fields.Many2many('account.journal',string='Journals')
    account_ids = fields.Many2many('account.account',string='Accounts')
    partner_ids = fields.Many2many('res.partner',string='Partners')
    filter_id = fields.Many2one('tw.account.report.filter', 'Filter')

    def action_download(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        if self.option == 'detail':
            return self._get_detail_report()
        else:
            return self._get_summary_report()
    
    def _get_where_clause(self):
        query_where = "WHERE 1=1 AND am.state = 'posted'"
        
        if self.company_ids:
            query_where += f" AND aml.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND aml.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.period_id:
            query_where += f" AND am.period_id = {self.period_id.id}"
        if self.journal_ids:
            query_where += f" AND am.journal_id IN ({', '.join(str(j.id) for j in self.journal_ids)})"
        
        if self.account_ids:
            query_where += f" AND aml.account_id IN ({', '.join(str(a.id) for a in self.account_ids)})"
        if self.partner_ids:
            query_where += f" AND aml.partner_id IN ({', '.join(str(p.id) for p in self.partner_ids)})"

        if self.start_date:
            query_where += f" AND am.date >= '{self.start_date}'"
        if self.end_date:
            query_where += f" AND am.date <= '{self.end_date}'"
            
        return query_where

    def _get_detail_report(self):
        query_where = self._get_where_clause()

        # Get summary header
        summary_header = self._get_summary_header_data()
        query = f"""
            SELECT 
                ap.code as period 
                , aa.code_store->>'1' as account_code
                , aa.name->>branch_partner.lang as account_name
                , branch.code as branch
                , am.division as division
                , COALESCE(LEFT(aa.code_store->>'1',6),'') || '-' || COALESCE(branch.profit_centre,'') || COALESCE(RIGHT(aa.sap,-6),'') as no_sun
                , am.date as tanggal
                , am.name as no_sistem
                , aml.name as name
                , aml.ref as reference
                , aml.debit as debit
                , aml.credit as credit
                , COALESCE(apr.reconcile_name,'') as reconcile_name
                , aj.name->>branch_partner.lang as journal 
                , rp.code as partner_code
                , rp.name as partner_name
                , pt.name->>branch_partner.lang as product_code
            FROM account_move_line aml
            LEFT JOIN account_move am ON am.id = aml.move_id 
            LEFT JOIN tw_account_period ap ON ap.id = am.period_id 
            LEFT JOIN account_account aa ON aa.id = aml.account_id 
            LEFT JOIN res_company branch ON branch.id = am.company_id
            LEFT JOIN res_partner branch_partner ON branch_partner.id = branch.partner_id  
            LEFT JOIN account_journal aj ON aj.id = am.journal_id 
            LEFT JOIN LATERAL (
                SELECT aml.id, string_agg(COALESCE(apr.full_reconcile_id::varchar,'P'||apr.id::varchar),',') as reconcile_name
                FROM account_partial_reconcile apr 
                WHERE (apr.debit_move_id = aml.id or apr.credit_move_id = aml.id)
            ) as apr ON apr.id = aml.id 
            LEFT JOIN res_partner rp ON rp.id = aml.partner_id 
            LEFT JOIN product_product pp ON pp.id = aml.product_id
            LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
            {query_where}
        """
        
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        
        start_date,end_date = self._get_date_range()
        return self.env['web.report'].sudo().generate_report('Report Journal',ress, data_summary_header=summary_header, start_date=start_date, end_date=end_date)
    
    def _get_summary_header_data(self):
        start_date,end_date = self._get_date_range()
        query_period = " "
        if self.period_id:
            query_period = f" AND ap.id = {self.period_id.id}"

        query =f"""
            SELECT 
            saldo.saldo_awal
            ,saldo.mutasi_debit
            ,saldo.mutasi_credit
            ,saldo.saldo_awal+saldo.mutasi_debit-saldo.mutasi_credit as saldo_akhir
            FROM (
                SELECT 
                    COALESCE(SUM(aml.debit-aml.credit) FILTER (WHERE aml.date < '{start_date}'),0) as saldo_awal,
                    COALESCE(SUM(aml.debit) FILTER (WHERE aml.date BETWEEN '{start_date}' AND '{end_date}' {query_period}),0) as mutasi_debit,
                    COALESCE(SUM(aml.credit) FILTER (WHERE aml.date BETWEEN '{start_date}' AND '{end_date}' {query_period}),0) as mutasi_credit 
                FROM account_move_line aml
                    LEFT JOIN account_move am ON am.id = aml.move_id 
                    LEFT JOIN tw_account_period ap ON ap.id = am.period_id 
                    LEFT JOIN account_account aa ON aa.id = aml.account_id 
                    LEFT JOIN res_company branch ON branch.id = am.company_id
                    LEFT JOIN res_partner branch_partner ON branch_partner.id = branch.partner_id  
                    LEFT JOIN account_journal aj ON aj.id = am.journal_id 
                    LEFT JOIN account_partial_reconcile apr ON apr.debit_move_id = aml.id or apr.credit_move_id = aml.id 
                    LEFT JOIN res_partner rp ON rp.id = aml.partner_id 
                    LEFT JOIN product_product pp ON pp.id = aml.product_id
                    LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                WHERE 1=1 AND am.state = 'posted'
            ) AS saldo
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchone()
        return {
            'B4':'Saldo Awal Tanggal :',
            'B5':'Mutasi Debit :',
            'B6':'Mutasi Credit :',
            'B7':'Saldo Akhir Tanggal:',
            'C4':ress.get('saldo_awal',0),
            'C5':ress.get('mutasi_debit',0),
            'C6':ress.get('mutasi_credit',0),
            'C7':ress.get('saldo_akhir',0),
        }
    
    def _get_date_range(self):
        if self.start_date:
            start_date = self.start_date.strftime('%Y-%m-%d')
        elif self.period_id:
            start_date = self.period_id.date_from.strftime('%Y-%m-%d')
        else:
            start_date = self._get_default_date().strftime('%Y-%m-%d')
        if self.end_date:
            end_date = self.end_date.strftime('%Y-%m-%d')
        elif self.period_id:
            end_date = self.period_id.date_to.strftime('%Y-%m-%d')
        else:
            end_date = self._get_default_date().strftime('%Y-%m-%d')
        return start_date,end_date

    @api.onchange('filter_id')
    def _onchange_filter_id(self):
        if self.filter_id:
            self.account_ids = [(6, 0, self.filter_id.account_ids.ids)]
        else:
            self.account_ids = [(5, 0, 0)]

    