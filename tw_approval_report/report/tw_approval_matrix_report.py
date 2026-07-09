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
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwApprovalMatrixReport(models.TransientModel):
    _name = "tw.approval.matrix.report"
    _description = "TW Approval Matrix Report"

    # 7: defaults methods
    @api.model
    def _get_default_date(self): 
        return datetime.now().date()
        
    @api.model
    def _get_date_min_30(self): 
        return datetime.now().date() + relativedelta(days=-30)

    def _set_domain_company_ids(self):
        return [('id','in',[b.id for b in self.env.user.company_ids])]
    
    def _domain_product(self):
        categ_ids = self.env['product.category'].get_child_ids('Unit')
        return [('categ_id','in',categ_ids)]

    # 8: fields
    name = fields.Char('Nama File', readonly=True)
    matrix_type = fields.Selection([
        ('biaya', 'Biaya'),
        ('discount', 'Discount'),
        ],default='biaya', string='Tipe Matrix') 
    report_type = fields.Selection([
        ('all', 'Semua di 1 sheet'),
        ('config', '1 config/product 1 sheet'),
        ('branch', '1 branch 1 sheet'),
        ],default='all', string='Tipe Output Laporan') 

    # 9: relation fields
    approval_config_ids = fields.Many2many('tw.approval.config', 'tw_matrix_approval_report_config_rel', 'wizard_id', 'approval_id', 'Config', copy=False)
    product_template_ids = fields.Many2many('product.template', 'tw_matrix_approval_report_product_template_rel', 'wizard_id', 'product_template_id', 'Product', domain=_domain_product,copy=False)
    company_ids = fields.Many2many('res.company', 'tw_matrix_approval_report_company_rel', 'wizard_id', 'company_id', "Branch", copy=False, domain=_set_domain_company_ids)

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods   
    def excel_report(self):
        date_today = datetime.now().strftime('%Y-%m-%d')
        if self.matrix_type == 'biaya':
            if self.report_type == 'all':
                data,data_sheet = self.export_report_biaya_all()
            elif self.report_type == 'branch':
                data,data_sheet = self.export_report_biaya_branch()
            elif self.report_type == 'config':
                data,data_sheet = self.export_report_biaya_config()
        elif self.matrix_type == 'discount':
            if self.report_type == 'all':
                data,data_sheet = self.export_report_discount_all()
            elif self.report_type == 'branch':
                data,data_sheet = self.export_report_discount_branch()
            elif self.report_type == 'config':
                data,data_sheet = self.export_report_discount_config()

        return self.env['web.report'].sudo().generate_report(report_name='Laporan Matrix Approval',data=data, data_sheet=data_sheet,data_summary_header=False,start_date=date_today, end_date=date_today)

    # 14: Private Methods
    def _check_child_company(self):
        child_company_ids = self.env['res.company'].search([('parent_id', 'in', self.company_ids.ids)]).ids
        return child_company_ids + self.company_ids.ids
