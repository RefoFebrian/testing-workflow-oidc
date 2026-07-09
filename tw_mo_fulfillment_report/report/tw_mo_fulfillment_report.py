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
class TwMoFulfillmentReport(models.TransientModel):
    _name = "tw.mo.fulfillment.report"
    _description = "TW MO Fulfillment Report"

    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now().date()

    # 8: fields
    start_date = fields.Date('Start Date',default=_get_default_date)
    end_date = fields.Date('End Date',default=_get_default_date)
    picking_type_code = fields.Selection([
        ('interbranch_in','Interbranch Receipts'),
        ('interbranch_out','Interbranch Deliveries')
    ], 'Picking Type', change_default=True)
    division_showroom = fields.Selection(string='Division Showroom', selection=lambda self: self.env['tw.selection'].get_division_options_list(['Unit','Umum']), default='Unit')
    division_workshop = fields.Selection(string='Division Workshop', selection=lambda self: self.env['tw.selection'].get_division_options_list(['Sparepart']), default='Sparepart')
    state = fields.Selection([
        ('assigned','Assigned'),
        ('done','Done')
    ], string='State')

    # 9: relation fields
    branch_sender_id = fields.Many2one('res.company', 'Branch Sender', required=True)
    branch_receiver_id = fields.Many2one('res.company', 'Branch Receiver', required=True)

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods
    def excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        division = ''
        if self._context.get('is_showroom',False):
            division = self.division_showroom
        elif self._context.get('is_workshop',False):
            division = self.division_workshop

        state = self.state
        start_date = self.start_date
        end_date = self.end_date     
        picking_type_code = self.picking_type_code 
        branch_sender = self.branch_sender_id   
        branch_receiver = self.branch_receiver_id  
   
        if not branch_sender and not branch_receiver:
            raise Warning('Perhatian! Branch Sender atau Branch Receiver belum diisi, harap isi terlebih dahulu')

        query = """
            SELECT 
            branch_sender.code as branch_sender
            , mo.division as division
            , mo.name as no_mo
            , mo.date as date_mo
            , branch_receiver.code as branch_receiver
            , sp.name as no_picking
            , sp.date as date_picking
            , sp.state as state
            , sp.date_done as date_done
            , pt.name->>'en_US' as template_name
            , p.default_code as default_code
            , mol.qty as qty
            , mo.division
            , COALESCE(mol.price,0) / (1 + (COALESCE(get_tax.amount,0)/100)) as price_unit
            , mol.qty * (COALESCE(mol.price,0) / (1 + (COALESCE(get_tax.amount,0)/100))) as sub_total
            FROM tw_mutation_order mo
            LEFT JOIN tw_mutation_order_line mol ON mo.id = mol.mutation_order_id
            LEFT JOIN stock_picking sp on sp.mutation_order_id = mo.id
            INNER JOIN stock_picking_type spt ON sp.picking_type_id = spt.id 
            LEFT JOIN res_company branch_receiver on sp.company_id = branch_receiver.id
            LEFT JOIN res_company branch_sender ON mo.company_id = branch_sender.id 
            LEFT JOIN product_product p ON mol.product_id = p.id 
            LEFT JOIN product_template pt on pt.id = p.product_tmpl_id
            LEFT JOIN (
                SELECT distinct ptr.prod_id as product_id, tax.amount
                FROM account_tax tax
                LEFT JOIN product_taxes_rel ptr on ptr.tax_id = tax.id
                WHERE tax.type_tax_use = 'sale'
            ) get_tax on get_tax.product_id = pt.id

            """

        query_where='WHERE 1 = 1'
        tz = '7 hours'

        if picking_type_code :
            if picking_type_code == 'in' :
                query_where += "  AND spt.code in ('incoming','interbranch_in')"
            elif picking_type_code == 'out' :
                query_where += "  AND spt.code in ('outgoing','interbranch_out')"
            else :
                query_where += "  AND spt.code = '%s'" % str(picking_type_code)

        if branch_sender :
            query_where += "  AND branch_sender.id in ('%s') " % branch_sender.id
          
        if branch_receiver :
            query_where += "  AND branch_receiver.id in ('%s') " % branch_receiver.id

        if division :
            query_where += "  AND mo.division = '%s'" % str(division)

        if state :
            query_where += "  AND sp.state = '%s'" % str(state)

        if start_date :
            query_where += " and sp.date >= '%s' " % start_date

        if end_date :
            end_date = end_date.strftime('%Y-%m-%d') + ' 23:59:59'
            query_where += " AND sp.date_done <= to_timestamp('%s', 'YYYY-MM-DD HH24:MI:SS') + interval '%s'" % (end_date,tz)

        query_order = "ORDER BY branch_sender.code, branch_receiver.code, mo.date, mo.name, sp.date, sp.date_done, pt.name"

        self._cr.execute(query+query_where+query_order)
        ress = self._cr.dictfetchall()

        return self.env['web.report'].sudo().generate_report('Report MO Fulfillment',ress, data_summary_header=False, start_date=start_date, end_date=end_date)
    