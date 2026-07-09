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
class TwMutationDetailReport(models.TransientModel):
    _name = "tw.mutation.detail.report"
    _description = "TW Mutation Detail Report"

    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now().date()

    # 8: fields
    start_date = fields.Date('Start Date',default=_get_default_date)
    end_date = fields.Date('End Date',default=_get_default_date)
    division_showroom = fields.Selection(string='Division Showroom', selection=lambda self: self.env['tw.selection'].get_division_options_list(['Unit','Umum']), default='Unit')
    division_workshop = fields.Selection(string='Division Workshop', selection=lambda self: self.env['tw.selection'].get_division_options_list(['Sparepart']), default='Sparepart')
    division = fields.Selection(string='Division',selection=lambda self: self.env['tw.selection'].get_division_options(), compute='_compute_division')
    options = fields.Selection([
        ('mutation_order_detil','Mutation Order Detil')
    ],default='mutation_order_detil')
    state = fields.Selection([('all','All'), ('confirm','Confirmed'), ('done','Done')],default='all')
    type_file = fields.Selection([('excel','Excel'),('csv','CSV')],string="Format File",default='excel')

    # 9: relation fields
    company_ids = fields.Many2many('res.company', 'tw_report_mutasi_detil_rel', 'tw_report_mutasi_detil_wizard_id','company_id', 'Branch', copy=False)
    product_ids = fields.Many2many('product.product', 'tw_report_mutasi_detil_product_rel', 'tw_report_mutasi_detil_wizard_id','product_id', 'Product', copy=False, )

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    @api.depends('division_workshop','division_showroom')
    def _compute_division(self):
        for record in self:
            if record._context.get('is_showroom',False):
                record.division = record.division_showroom
            elif record._context.get('is_workshop',False):
                record.division = record.division_workshop
            else:
                record.division = False

    # 12: Override Methods

    # 13: Action Methods
    def excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        start_date,end_date = self._get_date_range()

        query_where = ""
        query_division = ""
        query_saldo_where = ""
        if self.company_ids :
            query_where += " and mo.company_id IN %s " % str(tuple(self.company_ids.ids)).replace(',)', ')') 
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND mo.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.product_ids :
            query_where += " and mol.product_id IN %s " % str(tuple(self.product_ids.ids)).replace(',)', ')') 

        division = ''
        if self._context.get('is_showroom',False):
            division = self.division_showroom
        elif self._context.get('is_workshop',False):
            division = self.division_workshop
        
        if division:
            query_division = " and mo.division ='%s' " %(division)

        if self.state=='confirm':
            query_state = " and mo.state ='confirm' "
        elif self.state=='done':
            query_state = " and mo.state ='done' "
        else:
            query_state = " "
            
        query = f"""
            select b.code as branch_code
            , b.name as "Branch Name"
            , mo.division
            , mo.name as "Mutation Order"
            , mo.state 
            , to_char(mo.confirm_date + interval '7 hours', 'YYYY-MM-DD HH24:MI:SS') as confirm_date
            , b2.code as branch_req_code
            , b2.name as branch_req_name
            , pt.name->>'en_US' as name_template
            , pav.code as "PAV Code"
            , p.default_code
            , regexp_replace(pt.description->>'en_US', '<[^>]*>', '', 'g') as description
            , case when mo.state = 'cancelled' then -1 * mol.qty else mol.qty end as qty
            , case when p.division='Sparepart' then COALESCE(p.standard_price -> b.id::text, to_jsonb(0.0))::float else 0 end as hpp
            , mol.price as het
            , mol.price as harga_jual
            , case when p.division='Sparepart' then COALESCE(p.standard_price -> b.id::text, to_jsonb(0.0))::float * mol.qty else 0 end as total_hpp
            , (CASE 
                    WHEN mo.state = 'cancelled' THEN -1 * mol.qty 
                    ELSE mol.qty 
            END) * mol.price AS total_harga_jual
            , pc.name as categ1
            , coalesce(pc2.name, '') as categ2
            , mol.qty_supply as supply_qty
            , (CASE 
                    WHEN mo.state = 'cancelled' THEN -1 * mol.qty 
                    ELSE mol.qty 
            END) - mol.qty_supply AS undelivered
            FROM tw_mutation_order mo
            INNER JOIN tw_mutation_order_line mol on mol.mutation_order_id = mo.id
            INNER JOIN res_company b on b.id = mo.company_id
            LEFT JOIN res_partner b2 on b2.id = mo.requester_id
            LEFT JOIN product_product p on p.id = mol.product_id 
            LEFT JOIN product_template pt on pt.id = p.product_tmpl_id
            LEFT JOIN product_taxes_rel ptr ON ptr.prod_id = pt.id
            LEFT JOIN account_tax tax ON tax.id = ptr.tax_id
            LEFT JOIN product_category pc on pc.id = pt.categ_id
            LEFT JOIN product_category pc2 on pc2.id = pc.parent_id
            LEFT JOIN product_variant_combination vcom on vcom.product_product_id = p.id
            LEFT JOIN product_template_attribute_value ptav ON ptav.id = vcom.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id 
            where ((mo.state in ('done', 'confirm') and mo.date >= '{self.start_date}' and mo.date <= '{self.end_date}') 
            or (mo.state in ('cancelled') and mo.cancelled_date + interval '7 hours' >= '{self.start_date}' and mo.cancelled_date + interval '7 hours' <= '{self.end_date}'))
            {query_division}
            {query_where}
            {query_state}
            """

        if self._context.get('api_rpa'):
            return query
        
        self._cr.execute (query)
        ress = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Mutation Detail Report',ress, data_summary_header=False, start_date=start_date, end_date=end_date)

    def _get_date_range(self):
        if self.start_date:
            start_date = self.start_date.strftime('%Y-%m-%d')
        else:
            start_date = self._get_default_date().strftime('%Y-%m-%d')
        if self.end_date:
            end_date = self.end_date.strftime('%Y-%m-%d')
        else:
            end_date = self._get_default_date().strftime('%Y-%m-%d')
        return start_date,end_date
