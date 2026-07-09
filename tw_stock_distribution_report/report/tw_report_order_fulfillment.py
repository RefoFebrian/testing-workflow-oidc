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
class TwReportOrderFulfillmentWizard(models.TransientModel):
    _name = "tw.report.order.fulfillment.wizard"
    _description = "Report Order Fulfillment"

    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now()
    
    def _get_company_ids(self):
        company_ids_user = self.env.user.company_ids
        company_ids = [b.id for b in company_ids_user]
        return company_ids

    # 8: fields
    name = fields.Char('Filename', readonly=True)
    trx_type = fields.Selection([
        ('all','All'),
        ('mutation','Mutation Order'),
        ('sales','Sales Order')
    ], string='Transaction Type')
    division = fields.Selection([
        ('Unit','Unit'),
        ('Sparepart','Sparepart')
    ], string='Division')
    start_date = fields.Date('Start Date', default=datetime.today())
    end_date = fields.Date('End Date', default=datetime.today())

    # 9: relation fields
    company_ids = fields.Many2many('res.company', 'tw_stock_distribution_report_company_rel', 'tw_stock_distribution_report', 'company_id', "Branch", copy=False)

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods
    def excel_report(self,return_fp=False):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        start_date,end_date = self._get_date_range()
        
        company_ids = self.company_ids.ids
        trx_type = self.trx_type
        division = self.division

        query_where_so = " "
        query_where_mo = " "
        
        if division :
            query_where_so += " AND so.division = '%s'" % str(division)
            query_where_mo += " AND so.division = '%s'" % str(division)
        if start_date :
            query_where_so += " AND so.date_order >= '%s 00:00:00'" % str(start_date)
            query_where_mo += " AND so.date >= '%s'" % str(start_date)
        if end_date :
            query_where_so += " AND so.date_order <= to_timestamp('%s 23:59:59', 'YYYY-MM-DD HH24:MI:SS') + interval '7 hours'" % (end_date)
            query_where_mo += " AND so.date <= '%s'" % (end_date)
        if company_ids :
            query_where_so += " AND so.company_id in %s" % str(tuple(company_ids)).replace(',)', ')')
            query_where_mo += " AND so.company_id in %s" % str(tuple(company_ids)).replace(',)', ')')
        else:
            branch = self.env.user._get_company_ids()
            query_where_so += f" AND so.company_id IN {str(tuple(branch)).replace(',)', ')')}"
            query_where_mo += f" AND so.company_id IN {str(tuple(branch)).replace(',)', ')')}"
        query_order = " order by b.code, date_order, so.name, product_tmpl.name"
        query_sales = self._get_query_sales()+ query_where_so + query_order
        query_mo = self._get_query_mutation()+ query_where_mo + query_order
            
        query_all = """
            SELECT * 
            FROM ((%s) UNION (%s)) a
            ORDER BY branch_code, date_order, no_transaksi, kode_type
            """ % (query_sales, query_mo)
              
        if trx_type == 'sales'  :         
            self._cr.execute(query_sales)
            ress = self._cr.dictfetchall()
        elif trx_type == 'mutation'  :    
            self._cr.execute(query_mo)  
            ress = self._cr.dictfetchall()
        elif trx_type == 'all'  :    
            self._cr.execute(query_all)
            ress = self._cr.dictfetchall()
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self.env['web.report'].sudo().generate_report('Report Order Fulfillment',ress, data_summary_header=False, start_date=start_date, end_date=end_date, return_fp=return_fp)

    def _get_query_sales(self):
        query_sales = """
            select b.code as branch_code
            , so.name as no_transaksi
            , so.division
            , so.date_order + interval '7 hours' as date_order
            , so.state
            , partner.code as kode_dealer
            , partner.name as nama_dealer
            , product_tmpl.name->>'en_US' as kode_type
            , pav.code as kode_warna
            , sol.name as desc_type
            , sol.product_uom_qty as qty
            , coalesce(sol.qty_delivered,0) as qty_delivered
            , sol.product_uom_qty - coalesce(sol.qty_delivered,0) as qty_undelivered
            from tw_sale_order so
            inner join tw_sale_order_line sol on so.id = sol.order_id
            inner join res_company b on b.id = so.company_id
            left join res_partner partner on partner.id = so.partner_id
            LEFT JOIN product_product product ON sol.product_id = product.id 
            left JOIN product_template product_tmpl on product_tmpl.id = product.product_tmpl_id
            LEFT JOIN product_variant_combination vcom on vcom.product_product_id = product.id
            LEFT JOIN product_template_attribute_value ptav ON ptav.id = vcom.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id 
            where so.state in ('sale', 'done')
            and (sol.product_uom_qty != sol.qty_delivered or sol.qty_delivered is null)
        """
        return query_sales

    def _get_query_mutation(self):
        query_mo = """
            select b.code as branch_code
            , so.name as no_transaksi
            , so.division
            , so.date as date_order
            , so.state
            , partner.code as kode_dealer
            , partner.name as nama_dealer
            , product_tmpl.name->>'en_US' as kode_type
            , pav.code as kode_warna
            , sol.description as desc_type
            , sol.qty
            , coalesce(picking.qty,0) as qty_delivered
            , sol.qty - coalesce(picking.qty,0) as qty_undelivered
            from tw_mutation_order so
            inner join tw_mutation_order_line sol on so.id = sol.mutation_order_id
            inner join res_company b on b.id = so.company_id
            left join res_partner partner on partner.id = so.requester_id
            LEFT JOIN product_product product ON sol.product_id = product.id 
            left JOIN product_template product_tmpl on product_tmpl.id = product.product_tmpl_id
            LEFT JOIN product_variant_combination vcom on vcom.product_product_id = product.id
            LEFT JOIN product_template_attribute_value ptav ON ptav.id = vcom.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id 
            left join
            (select 
                pick.origin
                , move.product_id
                , sum(move.product_qty) qty
                from stock_picking pick
                inner join stock_move move on pick.origin = move.origin
                inner join stock_picking_type spt on pick.picking_type_id = spt.id
                where pick.state = 'done'
                and spt.code = 'outgoing'
                and pick.mutation_order_id = pick.id
                group by pick.origin, move.product_id
            ) picking on picking.origin = so.name and picking.product_id = sol.product_id
            where so.state in ('confirm', 'done')
            and sol.qty > 0 and (sol.qty != picking.qty or picking.qty is null) 
        """
        return query_mo

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