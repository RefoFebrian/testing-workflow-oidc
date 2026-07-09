# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import UserError as Warning

class ApiPopeyeReport(models.TransientModel):
    _name = "tw.api.popeye.report"
    _description = "API Popeye Report"
    _rec_name = "file"

    def _get_default_date(self):
        return fields.Date.today()
    
    file = fields.Char('File Name')
    data_x = fields.Binary('File', readonly=True)
    state_x = fields.Selection([('choose','choose'), ('get','get')], default='choose')
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    option = fields.Selection([
        ('all', 'ALL'),
        ('supplier_payment', 'Supplier Payment'),
        ('bank_transfer', 'Bank Transfer')
    ], string='Option', default='all')
    type = fields.Selection([
        ('all', 'ALL'),
        ('send_to_popeye', 'Sudah Kirim ke Popeye'),
    ], string='Type', default='send_to_popeye')
    company_ids = fields.Many2many('res.company', 'tw_api_popeye_report_company_rel', 'popeye_report_id', 'company_id', default=lambda self: self.env.user.company_id)
    

    def generate_data(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        query_where = ''
        
        # Handle empty company_ids - use all companies if none selected
        if self.company_ids:
            company_ids = self.company_ids.ids
        else:
            company_ids = self.env['res.company'].search([]).ids
        
        # Format tuple for SQL - handle single element tuple
        if len(company_ids) == 1:
            company_ids_str = "(%s)" % company_ids[0]
        else:
            company_ids_str = str(tuple(company_ids))
        
        query_supplier_payment = """
            SELECT
                rp.name as "Nama Partner"
                , rp.email as "Email"
                , '[' || wb.code || '] ' || wb.name as "Cabang"
                , '[' || wbu.code || '] ' || wbu.name as "Cabang Untuk"
                , wav.name as "Number"
                , wav.date as "Tanggal"
                , wav.state as "Status Transaksi"
                , wav.status_api_payment as "Status Popeye"
                , aj.name->>'en_US' as "Payment Method"
                , wav.amount as "Paid Amount/Total"
                , ru.login as "Send To Popeye By"
                , bank.acc_number as "No. Rekening Tujuan"
                , wav.memo as "Description"
            FROM tw_account_payment wav 
            LEFT JOIN res_partner rp ON wav.partner_id = rp.id
            LEFT JOIN res_company wb ON wav.company_id = wb.id
            LEFT JOIN res_company wbu ON wav.beneficiary_company_id = wbu.id 
            LEFT JOIN account_journal aj ON wav.journal_id = aj.id
            LEFT JOIN res_users ru ON wav.send_uid = ru.id
            LEFT JOIN res_partner rp2 ON ru.partner_id = rp2.id
            LEFT JOIN res_partner_bank bank ON bank.id = wav.partner_bank_id
            WHERE 1=1
            AND wav.type in ('supplier_payment', 'customer_payment')
            AND wav.date BETWEEN '{start_date}' AND '{end_date}'
            AND wav.company_id IN {company_ids}
            AND wav.status_api_payment != 'draft'
        """.format(start_date=self.start_date, end_date=self.end_date, company_ids=company_ids_str)
        
        query_bank_transfer = """
            SELECT
                rp.name as "Nama Partner"
                , wbt.email as "Email"
                , '[' || wb.code || '] ' || wb.name as "Cabang"
                , NULL as "Cabang Untuk"
                , wbt.name as "Number"
                , wbt.date as "Tanggal"
                , wbt.state as "Status Transaksi"
                , wbt.status_api_payment as "Status Popeye"
                , aj.name->>'en_US' as "Payment Method"
                , wbt.amount as "Paid Amount/Total"
                , rp2.name as "Send To Popeye By"
                , bank.acc_number as "No. Rekening Tujuan"
                , wbt.description as "Description"
            FROM tw_bank_transfer wbt
            LEFT JOIN res_partner rp ON wbt.partner_id = rp.id
            LEFT JOIN res_company wb ON wbt.company_id = wb.id
            LEFT JOIN account_journal aj ON wbt.journal_id = aj.id
            LEFT JOIN res_users ru ON wbt.send_uid = ru.id
            LEFT JOIN res_partner rp2 ON ru.partner_id = rp2.id
            LEFT JOIN res_partner_bank bank ON bank.id = wbt.partner_bank_id
            WHERE 1=1
            AND wbt.date between '{start_date}' AND '{end_date}'
            AND wbt.company_id IN {company_ids}
            AND wbt.status_api_payment != 'draft'
        """.format(start_date=self.start_date, end_date=self.end_date, company_ids=company_ids_str)
        
        if self.option == 'supplier_payment':
            if self.type == 'send_to_popeye':
                query_where += "  AND wav.status_api_payment != 'draft'"
            query = """
                {query_supplier_payment}
                {query_where}
            """.format(query_supplier_payment=query_supplier_payment, query_where=query_where)            
        elif self.option == 'bank_transfer':
            if self.type == 'send_to_popeye':
                query_where += " AND wbt.status_api_payment != 'draft'"
            query = """
                {query_bank_transfer}
                {query_where}
            """.format(query_bank_transfer=query_bank_transfer, query_where=query_where)            
        else:
            query_where_sp = ''
            query_where_bt = ''
            if self.type == 'send_to_popeye':
                query_where_sp += " AND wav.status_api_payment != 'draft'"
                query_where_bt += " AND wbt.status_api_payment != 'draft'"
            query = """
                {query_supplier_payment}
                {query_where_sp}
                UNION
                {query_bank_transfer}
                {query_where_bt}
            """.format(query_supplier_payment=query_supplier_payment, query_where_sp=query_where_sp, query_bank_transfer=query_bank_transfer, query_where_bt=query_where_bt)
        
        self._cr.execute(query)
        ress = self._cr.dictfetchall() 

        return self.env['web.report'].sudo().generate_report('Report Popeye', ress)
