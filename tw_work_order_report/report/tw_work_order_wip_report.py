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
class TwWorkOrderWIPRerport(models.TransientModel):
    _name = "tw.work.order.wip.report"
    _description = "Report Work Order WIP"

    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now()
    
    # 8: fields
    name = fields.Char('File Name')
    start_date = fields.Date('Start Date', default=lambda self: self._get_default_date().replace(day=1))
    end_date = fields.Date('End Date', default=_get_default_date)

    # 9: relation fields
    company_ids = fields.Many2many('res.company',string="Branch",required=True)

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods
    def excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        # Querry
        company_ids = [b.id for b in self.company_ids]
        query_where = " WHERE 1=1"
        if company_ids :
            query_where += " AND company.id in %s " % str(tuple(company_ids)).replace(',)', ')')        

        if self.start_date:
            query_where += " AND wo.date >= '%s'" % self.start_date.strftime('%Y-%m-%d')
        if self.end_date:
            query_where += " AND wo.date <= '%s'" % self.end_date.strftime('%Y-%m-%d')
        query_where += " AND wo.state in ('waiting_for_approval', 'confirmed', 'approved', 'finished')"

        query = """
            SELECT company.code as branch_code
            , company.name as branch_name
            , wo.name as wo_name
            , wo.division as wo_division
            , wo.date as wo_date
            , CASE WHEN wo.type = 'REG' THEN 'Regular'
                WHEN wo.type = 'WAR' THEN 'Job Return'
                WHEN wo.type = 'CLA' THEN 'Claim'
                WHEN wo.type = 'SLS' THEN 'Part Sales'
                ELSE wo.type
            END as wo_type
            , wo.state as wo_state
            , partner.code as partner_code
            , partner.name as partner_no
            , lot.plate_number as no_polisi
            , lot.name as engine_no
            , lot.chassis_number as no_chassis
            , unit_t.name->>'en_US' as unit_type
            , emp.identification_id as nip
            , res.name as mechanic_name
            , wo.start_date + interval '7 hours' as start
            , wo.break_date + interval '7 hours' as date_break
            , wo.end_break_date + interval '7 hours' as end_break
            , wo.finish_date + interval '7 hours' as finish
            , wol.division as division
            , pt.name->>'en_US' as product_template
            , pt.description->>'en_US' as description
            , wol.product_uom_qty as quantity
            , wol.price_unit as price_unit
            , wol.price_unit / (1 + COALESCE(tax.amount,0)) * wol.product_uom_qty as nett_sales
            , wol.discount as discount
            , (wol.price_unit * (1 - coalesce(wol.discount,0) / 100)) / (1 + COALESCE(tax.amount,0)) * wol.product_uom_qty as subtotal
            , coalesce(wol.qty_delivered, 0) as supply_qty
            , (wol.price_unit * (1 - coalesce(wol.discount,0) / 100)) / (1 + COALESCE(tax.amount,0)) * wol.qty_delivered as stock_wip
            FROM tw_work_order wo
            INNER JOIN tw_work_order_line wol on wo.id = wol.order_id
            INNER JOIN res_company company on company.id = wo.company_id
            LEFT JOIN account_tax_tw_work_order_line_rel as wot on wot.tw_work_order_line_id = wol.id
            LEFT JOIN account_tax as tax on tax.id = wot.account_tax_id
            LEFT JOIN res_partner partner on partner.id = wo.partner_id
            LEFT JOIN stock_lot lot on lot.id = wo.lot_id
            LEFT JOIN product_product unit on unit.id = wo.product_id
            LEFT JOIN product_template unit_t on unit_t.id = unit.product_tmpl_id
            LEFT JOIN res_users mechanic on mechanic.id = wo.mechanic_id
            LEFT JOIN resource_resource res on res.user_id = mechanic.id
            LEFT JOIN hr_employee emp on res.id = emp.resource_id
            LEFT JOIN product_product prod on prod.id = wol.product_id
            LEFT JOIN product_template pt on pt.id = prod.product_tmpl_id
            %s
            ORDER BY company.code,wo.date,wo.name,wol.division
        """ %(query_where)

        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        
        start_date,end_date = self._get_date_range()
        return self.env['web.report'].sudo().generate_report('Report WIP',ress, data_summary_header=False, start_date=start_date, end_date=end_date)
        
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
    
    