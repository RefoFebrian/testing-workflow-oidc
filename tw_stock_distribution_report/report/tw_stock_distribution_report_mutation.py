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
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwStockDistributionReport(models.TransientModel):
    _inherit = "tw.stock.distribution.report"
    _description = "Report Stock Distribution"

    trx_type = fields.Selection(selection_add=[('mutation','Mutation')])

    # Inherit method
    def _get_query_report_order(self, trx_type, order_state, query_where):
        query_sales = super()._get_query_report_order(trx_type, order_state, query_where)
        query = ""
        query_mutation = ""
        if trx_type == 'mutation' or trx_type == 'all' or trx_type == False :
            query_mutation = """
                (select b.code as branch_code
                , b.name as branch_name
                , dealer.code as dealer_code
                , dealer.name as dealer_name
                , CASE WHEN sd.requester_id IS NOT NULL THEN 'Mutation' ELSE 'Sales' END as transaction_type
                , sd.division
                , sd.name as stock_distribution
                , sd.date
                , sd.state as distribution_state
                , sd.start_date
                , sd.end_date
                , sd.description
                , so.name as order_name
                , so.date as order_date
                , so.state as order_state
                , prod_template.default_code as product
                , COALESCE(pav.code,'') as color
                , prod_cat.name as category
                , COALESCE(sol.qty, 0) as qty
                , COALESCE(sol.price, 0) as unit_price
                , 0 as discount
                , COALESCE(sol.qty, 0)*COALESCE(sol.price, 0) as est_amount
                , COALESCE(sol.qty_supply,0) as supplied_qty
                , COALESCE(sol.qty, 0)*COALESCE(sol.price, 0) as est_supplied_amount
                , COALESCE(sol.qty, 0)-COALESCE(sol.qty, 0) as outstanding_qty
                , COALESCE(sol.price, 0)*(COALESCE(sol.qty, 0)-COALESCE(sol.qty, 0)) as est_outstanding_amount
                from tw_stock_distribution sd
                left join res_company b on sd.company_id = b.id
                --TODO: dealer_id tidak ada jadinya menggunakan requester_id apakah perlu penyesuaian?
                left join res_partner dealer on sd.requester_id = dealer.id
                left join tw_mutation_order so on sd.id = so.stock_distribution_id
                left join tw_mutation_order_line sol on so.id = sol.mutation_order_id
                left join product_product product on sol.product_id = product.id
                LEFT JOIN product_variant_combination vcom on vcom.product_product_id = product.id
                LEFT JOIN product_template_attribute_value ptav ON ptav.id = vcom.product_template_attribute_value_id
                LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id 
                left join product_template prod_template on product.product_tmpl_id = prod_template.id
                left join product_category prod_cat on prod_template.categ_id = prod_cat.id
                where sd.requester_id IS NOT NULL
                %s
                order by branch_code, dealer_code, date, sd.name, order_date, order_name)
            """ % (query_where)

        if trx_type == 'mutation' :
            query = query_mutation
        elif trx_type == 'all' :
            query = """
                select * from (%s UNION %s) a
                order by branch_code, dealer_code, date, stock_distribution, order_date, order_name
            """ % (query_mutation, query_sales)
        return query if query else query_sales