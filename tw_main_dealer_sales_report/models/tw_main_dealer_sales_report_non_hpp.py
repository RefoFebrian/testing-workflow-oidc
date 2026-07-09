# -*- coding: utf-8 -*-

import base64
import csv

from datetime import datetime
from io import StringIO
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning


class tw_main_dealer_sales_report(models.TransientModel):
    _inherit = "tw.main.dealer.sales.report"

    def _print_excel_report_non_hpp(self):
        query_where = " WHERE 1=1 "
        query_where_cancel = " "

        if self.product_ids:
            query_where += " AND sol.product_id IN %s" % str(tuple(self.product_ids.ids)).replace(',)', ')')
        if self.division:
            query_where += " AND so.division = '%s'" % str(self.division)
        if self.start_date:
            query_where_cancel += " AND soc.date >= '%s'" % str(self.start_date)
            query_where += " AND so.date_order + INTERVAL '7 hours' >= to_timestamp('%s 00:00:01', 'YYYY-MM-DD HH24:MI:SS')" % str(self.start_date)
        if self.end_date:
            query_where_cancel += " AND soc.date <= '%s'" % str(self.end_date)
            query_where += " AND so.date_order + INTERVAL '7 hours' <= to_timestamp('%s 23:59:59', 'YYYY-MM-DD HH24:MI:SS')" % str(self.end_date)
        if self.state in ['waiting_for_approval', 'approved','sale','cancel','unused']:
            query_where += " AND so.state = ('%s')" % str(self.state)
        elif self.state == 'all':
            query_where += " AND so.state in ('waiting_for_approval', 'approved','sale','cancel')"
        else:
            query_where += " AND so.state in ('waiting_for_approval','approved','sale')"
        if self.company_ids:
            query_where += " AND so.company_id IN %s" % str(tuple(self.company_ids.ids)).replace(',)', ')')
        else:
            companies = self.env.user._get_company_ids()
            query_where += f" AND so.company_id IN {str(tuple(companies)).replace(',)', ')')}"
            
        if self.dealer_ids:
            query_where += " AND so.partner_id IN %s" % str(tuple(self.dealer_ids.ids)).replace(',)', ')')
        
        query_where += " AND so.confirm_date is not null"
        query_order_by = " ORDER BY b.code"

        query_sales = ""
        query_cancel = ""

        if self.division == 'Unit':
            query_sales = """
            SELECT 
                b.code as branch_code, 
                b.name as branch_name, 
                so.name as so_number, 
                CASE WHEN so.state = 'sale' THEN 'Sales Order'
                    WHEN so.state = 'cancel' THEN 'Cancel'
                    WHEN so.state = 'unused' THEN 'Unused'
                    WHEN so.state IS NULL THEN '' 
                ELSE so.state END as state,
                to_char(so.date_order + interval '7 hours', 'YYYY-MM-DD HH12:MI AM') as date_order, 
                customer.code as cust_code, 
                customer.name as cust_name, 
                prod.default_code as type, 
                COALESCE(warna_unit.name->>'en_US', warna_unit.name->>'id_ID') as warna,
                sol.product_uom_qty as qty,
                sol.price_unit as harga_jual, 
                sol.discount as disc,
                sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) as harga_jual_excl_tax,
                sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty as nett_sales,
                COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty as discount_cash_avg,
                COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty as discount_lain_avg,
                COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty as discount_program_avg,
                (sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty) as dpp,
                ((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty)) * COALESCE(tax.amount,0)/100 as tax,
                ((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty)) * (1 + COALESCE(tax.amount,0)/100) as total,
                COALESCE(prod_category.name,'') as category,
                COALESCE(prod_category2.name,'') as parent_category,
                COALESCE(series_id.name->>'en_US', series_id.name->>'id_ID') as prod_series,
                invs.ref as no_invoice,
                COALESCE(fp.name,'') as faktur_pajak, 
                0 as soc_id
                from tw_sale_order so
                INNER JOIN tw_sale_order_line sol on so.id = sol.order_id
                LEFT JOIN account_tax_tw_sale_order_line_rel tdsoltr ON tdsoltr.tw_sale_order_line_id = sol.id
				LEFT JOIN account_tax tax ON tax.id = tdsoltr.account_tax_id
				left join (select sale_order_id, SUM(case when name = 'Discount Cash' then amount else 0 end) as discount_cash,
				SUM(case when name = 'Discount Lain' then amount else 0 end) as discount_lain,
				SUM(case when name = 'Discount Program' then amount else 0 end) as discount_program
				from tw_sale_order_discount group by sale_order_id) sod on so.id = sod.sale_order_id
                LEFT JOIN tw_stock_distribution sd on so.id = sd.sale_order_id
                LEFT JOIN account_move as invs ON invs.invoice_origin=so.name and invs.state != 'draft' and invs.move_type = 'out_invoice'
                INNER JOIN (select tent_so.id, COALESCE(sum(tent_sol.product_uom_qty),0) as total_qty from tw_sale_order tent_so INNER JOIN tw_sale_order_line tent_sol on tent_so.id = tent_sol.order_id group by tent_so.id) as tent on so.id = tent.id
                LEFT JOIN res_company b on so.company_id = b.id
                LEFT JOIN res_partner customer on so.partner_id = customer.id
                LEFT JOIN product_product prod on sol.product_id = prod.id
                LEFT JOIN product_template prod_template on prod.product_tmpl_id = prod_template.id
                LEFT JOIN product_series as series_id ON series_id.id = prod_template.series_id
                LEFT JOIN (SELECT DISTINCT ON (product_tmpl_id) * FROM product_template_attribute_value ORDER BY product_tmpl_id, id) AS f ON f.product_tmpl_id = prod_template.id
                LEFT JOIN product_attribute_value warna_unit ON warna_unit.id = f.product_attribute_value_id
                LEFT JOIN product_category prod_category on prod_template.categ_id = prod_category.id
                LEFT JOIN product_category prod_category2 on prod_template.categ_id = prod_category2.id
                LEFT JOIN tw_faktur_pajak_out fp on so.faktur_pajak_out_id = fp.id
                %s %s
            """ % (query_where, query_order_by)
        else:
            query_sales = """
            SELECT 
                b.code as branch_code, 
                b.name as branch_name, 
                so.name as so_number, 
                CASE WHEN so.state = 'sale' THEN 'Sales Order'
                    WHEN so.state = 'cancel' THEN 'Cancel'
                    WHEN so.state = 'unused' THEN 'Unused'
                    WHEN so.state IS NULL THEN '' 
                ELSE so.state END as so_state,
                to_char(so.date_order + interval '7 hours', 'YYYY-MM-DD HH12:MI AM') as date_order, 
                customer.code as cust_code, 
                customer.name as cust_name, 
                prod.default_code as product_template,
                '' as warna,
                sol.product_uom_qty as qty,
                sol.price_unit as harga_jual, 
                sol.discount as disc,
                sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) as harga_jual_excl_tax,
                sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty as nett_sales,
                COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty as discount_cash_avg,
                COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty as discount_lain_avg,
                COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty as discount_program_avg,
                (sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty) as dpp,
                ((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty)) * COALESCE(tax.amount,0)/100 as tax,
                ((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty)) * (1 + COALESCE(tax.amount,0)/100) as total,
                COALESCE(prod_category.name,'') as category,
                COALESCE(prod_category2.name,'') as parent_category,
                COALESCE(series_id.name->>'en_US', series_id.name->>'id_ID') as prod_series,
                invs.ref as no_invoice,
                COALESCE(fp.name,'') as faktur_pajak, 
                0 as soc_id
                from tw_sale_order so
                INNER JOIN tw_sale_order_line sol on so.id = sol.order_id
                LEFT JOIN account_tax_tw_sale_order_line_rel tdsoltr ON tdsoltr.tw_sale_order_line_id = sol.id
			    LEFT JOIN account_tax tax ON tax.id = tdsoltr.account_tax_id
				left join (select sale_order_id, SUM(case when name = 'Discount Cash' then amount else 0 end) as discount_cash,
				SUM(case when name = 'Discount Lain' then amount else 0 end) as discount_lain,
				SUM(case when name = 'Discount Program' then amount else 0 end) as discount_program
				from tw_sale_order_discount group by sale_order_id) sod on so.id = sod.sale_order_id
                LEFT JOIN tw_stock_distribution sd on so.id = sd.sale_order_id
                LEFT JOIN account_move as invs ON invs.invoice_origin=so.name and invs.state != 'draft' and invs.move_type = 'out_invoice'
                INNER JOIN (select tent_so.id, COALESCE(sum(tent_sol.product_uom_qty),0) as total_qty from tw_sale_order tent_so INNER JOIN tw_sale_order_line tent_sol on tent_so.id = tent_sol.order_id group by tent_so.id) as tent on so.id = tent.id
                LEFT JOIN res_company b on so.company_id = b.id
                LEFT JOIN res_partner customer on so.partner_id = customer.id
                LEFT JOIN product_product prod on sol.product_id = prod.id
                LEFT JOIN product_template prod_template on prod.product_tmpl_id = prod_template.id
                LEFT JOIN product_series as series_id ON series_id.id = prod_template.series_id
                LEFT JOIN (SELECT DISTINCT ON (product_tmpl_id) * FROM product_template_attribute_value ORDER BY product_tmpl_id, id) AS f ON f.product_tmpl_id = prod_template.id
                LEFT JOIN product_attribute_value warna_unit ON warna_unit.id = f.product_attribute_value_id
                LEFT JOIN product_category prod_category on prod_template.categ_id = prod_category.id
                LEFT JOIN product_category prod_category2 on prod_template.categ_id = prod_category2.id
                LEFT JOIN tw_faktur_pajak_out fp on so.faktur_pajak_out_id = fp.id
                %s %s
            """ % (query_where, query_order_by)
        
        if self.state in ('all','cancel'):
            if self.division == 'Unit':
                query_cancel = """
                    SELECT 
                        b.code as branch_code, 
                        b.name as branch_name, 
                        so.name as so_number, 
                        CASE WHEN so.state = 'sale' THEN 'Sales Order'
                            WHEN so.state = 'cancel' THEN 'Cancel'
                            WHEN so.state = 'unused' THEN 'Unused'
                            WHEN so.state IS NULL THEN '' 
                        ELSE so.state END as state,
                        to_char(so.date_order + interval '7 hours', 'YYYY-MM-DD HH12:MI AM') as date_order, 
                        customer.code as cust_code, 
                        customer.name as cust_name, 
                        prod.default_code as type, 
                        COALESCE(warna_unit.name->>'en_US', warna_unit.name->>'id_ID') as warna,
                        (sol.product_uom_qty) *-1 as qty,
                        (sol.price_unit) *-1 as harga_jual, 
                        (sol.discount) *-1 as disc,
                        (sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100)) *-1 as harga_jual_excl_tax,
                        (sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) *-1 as nett_sales,
                        (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) *-1 as discount_cash_avg,
                        (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) *-1 as discount_lain_avg,
                        COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty as discount_program_avg,
                        ((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty)) *-1 as dpp,
                        (((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty)) * COALESCE(tax.amount,0)/100)*-1 as tax,
                        (((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty)) * (1 + COALESCE(tax.amount,0)/100))*-1 as total,
                        COALESCE(prod_category.name,'') as category,
                        COALESCE(prod_category2.name,'') as parent_category,
                        COALESCE(series_id.name->>'en_US', series_id.name->>'id_ID') as prod_series,
                        invs.ref as no_invoice,
                        COALESCE(fp.name,'') as faktur_pajak, 
                        0 as soc_id
                        from tw_cancellation soc
                        INNER JOIN tw_sale_order so on soc.transaction_name = so.name
                        INNER JOIN tw_sale_order_line sol on so.id = sol.order_id
                        LEFT JOIN account_tax_tw_sale_order_line_rel tdsoltr ON tdsoltr.tw_sale_order_line_id = sol.id
				        LEFT JOIN account_tax tax ON tax.id = tdsoltr.account_tax_id
                        left join (select sale_order_id, SUM(case when name = 'Discount Cash' then amount else 0 end) as discount_cash,
                        SUM(case when name = 'Discount Lain' then amount else 0 end) as discount_lain,
                        SUM(case when name = 'Discount Program' then amount else 0 end) as discount_program
                        from tw_sale_order_discount group by sale_order_id) sod on so.id = sod.sale_order_id
                        LEFT JOIN tw_stock_distribution sd on so.id = sd.sale_order_id
                        LEFT JOIN account_move as invs ON invs.invoice_origin=so.name and invs.state != 'draft' and invs.move_type = 'out_invoice'
                        INNER JOIN (select tent_so.id, COALESCE(sum(tent_sol.product_uom_qty),0) as total_qty from tw_sale_order tent_so INNER JOIN tw_sale_order_line tent_sol on tent_so.id = tent_sol.order_id group by tent_so.id) as tent on so.id = tent.id
                        LEFT JOIN res_company b on so.company_id = b.id
                        LEFT JOIN res_partner customer on so.partner_id = customer.id
                        LEFT JOIN product_product prod on sol.product_id = prod.id
                        LEFT JOIN product_template prod_template on prod.product_tmpl_id = prod_template.id
                        LEFT JOIN product_series as series_id ON series_id.id = prod_template.series_id
                        LEFT JOIN (SELECT DISTINCT ON (product_tmpl_id) * FROM product_template_attribute_value ORDER BY product_tmpl_id, id) AS f ON f.product_tmpl_id = prod_template.id
                        LEFT JOIN product_attribute_value warna_unit ON warna_unit.id = f.product_attribute_value_id
                        LEFT JOIN product_category prod_category on prod_template.categ_id = prod_category.id
                        LEFT JOIN product_category prod_category2 on prod_template.categ_id = prod_category2.id
                        LEFT JOIN tw_faktur_pajak_out fp on so.faktur_pajak_out_id = fp.id
                    %s %s %s
                """ % (query_where_cancel,query_where,query_order_by)
            else:
                query_cancel="""
                    SELECT 
                        b.code as branch_code, 
                        b.name as branch_name, 
                        so.name as so_number, 
                        CASE WHEN so.state = 'sale' THEN 'Sales Order'
                            WHEN so.state = 'cancel' THEN 'Cancel'
                            WHEN so.state = 'unused' THEN 'Unused'
                            WHEN so.state IS NULL THEN '' 
                        ELSE so.state END as so_state,
                        to_char(so.date_order + interval '7 hours', 'YYYY-MM-DD HH12:MI AM') as date_order, 
                        customer.code as cust_code, 
                        customer.name as cust_name, 
                        prod.default_code as product_template,
                        '' as warna,
                        (sol.product_uom_qty)*-1 as qty,
                        (sol.price_unit) *-1 as harga_jual, 
                        (sol.discount)*-1 as disc,
                        (sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100)) *-1 as harga_jual_excl_tax,
                        (sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty)*-1 as nett_sales,
                        (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty)*-1 as discount_cash_avg,
                        (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty)*-1 as discount_lain_avg,
                        (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty)*-1 as discount_program_avg,
                        ((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty))*-1 as dpp,
                        (((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty)) * COALESCE(tax.amount,0)/100)*-1 as tax,
                        (((sol.price_unit * (1 - COALESCE(sol.discount,0) / 100) / (1 + COALESCE(tax.amount,0)/100) * sol.product_uom_qty) - (COALESCE(sod.discount_cash,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_lain,0) / tent.total_qty * sol.product_uom_qty) - (COALESCE(sod.discount_program,0) / tent.total_qty * sol.product_uom_qty)) * (1 + COALESCE(tax.amount,0)/100))*-1 as total,
                        COALESCE(prod_category.name,'') as category,
                        COALESCE(prod_category2.name,'') as parent_category,
                        COALESCE(series_id.name->>'en_US', series_id.name->>'id_ID') as prod_series,
                        invs.ref as no_invoice,
                        COALESCE(fp.name,'') as faktur_pajak, 
                        0 as soc_id
                        from tw_cancellation soc
                        INNER JOIN tw_sale_order so on soc.transaction_name = so.name
                        INNER JOIN tw_sale_order_line sol on so.id = sol.order_id
                        LEFT JOIN account_tax_tw_sale_order_line_rel tdsoltr ON tdsoltr.tw_sale_order_line_id = sol.id
				        LEFT JOIN account_tax tax ON tax.id = tdsoltr.account_tax_id
                        left join (select sale_order_id, SUM(case when name = 'Discount Cash' then amount else 0 end) as discount_cash,
                        SUM(case when name = 'Discount Lain' then amount else 0 end) as discount_lain,
                        SUM(case when name = 'Discount Program' then amount else 0 end) as discount_program
                        from tw_sale_order_discount group by sale_order_id) sod on so.id = sod.sale_order_id
                        LEFT JOIN tw_stock_distribution sd on so.id = sd.sale_order_id
                        LEFT JOIN account_move as invs ON invs.invoice_origin=so.name and invs.state != 'draft' and invs.move_type = 'out_invoice'
                        INNER JOIN (select tent_so.id, COALESCE(sum(tent_sol.product_uom_qty),0) as total_qty from tw_sale_order tent_so INNER JOIN tw_sale_order_line tent_sol on tent_so.id = tent_sol.order_id group by tent_so.id) as tent on so.id = tent.id
                        LEFT JOIN res_company b on so.company_id = b.id
                        LEFT JOIN res_partner customer on so.partner_id = customer.id
                        LEFT JOIN product_product prod on sol.product_id = prod.id
                        LEFT JOIN product_template prod_template on prod.product_tmpl_id = prod_template.id
                        LEFT JOIN product_series as series_id ON series_id.id = prod_template.series_id
                        LEFT JOIN (SELECT DISTINCT ON (product_tmpl_id) * FROM product_template_attribute_value ORDER BY product_tmpl_id, id) AS f ON f.product_tmpl_id = prod_template.id
                        LEFT JOIN product_attribute_value warna_unit ON warna_unit.id = f.product_attribute_value_id
                        LEFT JOIN product_category prod_category on prod_template.categ_id = prod_category.id
                        LEFT JOIN product_category prod_category2 on prod_template.categ_id = prod_category2.id
                        LEFT JOIN tw_faktur_pajak_out fp on so.faktur_pajak_out_id = fp.id
                    %s %s %s
                """ % (query_where_cancel, query_where, query_order_by)
        if self.state == 'cancel':
            query = query_cancel
        elif self.state == 'all':
            query="""
                SELECT * FROM ((%s) UNION (%s)) a
                ORDER BY branch_code, date_order
            """ % (query_sales, query_cancel)
        else:
            query=query_sales

        if self.type_file == 'excel':
            self.env.cr.execute(query)
            rows = self.env.cr.dictfetchall()
            if not rows:
                raise Warning('Data tidak ada...')
            report_name = f"Laporan Penjualan MD"
            return self.env['web.report'].sudo().generate_report(report_name, rows,show_total_footer=True,freeze_panes_column=3)
        else:
            fp = StringIO()
            self.env.cr.execute(query)
            rows = self.env.cr.fetchall()
            if not rows:
                raise Warning('Data tidak ada...')
       
            writer = csv.writer(fp, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["Branch Code", "Branch Name", "SO Number", "State", "Date", "Customer Code",
                                 "Customer Name", "Type", "Color", "Qty", "Harga Jual", "Disc (%)",
                                 "Harga Jual Excl Tax", "Sales", "Disc Cash (Avg)", "Disc Lain (Avg)",
                                 "Disc Program (Avg)", "DPP", "Tax", "Total Piutang", "Category Name", 
                                 "Parent Category Name", "Sales", "No Invoice", "Faktur Pajak"])
                
            for res in rows:
                branch_code = str(res[0].encode('ascii','ignore').decode('ascii')) if res[0] != None else ''
                branch_name = str(res[1].encode('ascii','ignore').decode('ascii')) if res[1] != None else ''
                name = str(res[2].encode('ascii','ignore').decode('ascii')) if res[2] != None else ''
                state = str(res[3].encode('ascii','ignore').decode('ascii')) if res[3] != None else ''
                date_order = datetime.strptime(res[4][0:22], "%Y-%m-%d %I:%M %p") if res[4] else ''
                cust_code = str(res[5].encode('ascii','ignore').decode('ascii')) if res[5] != None else ''
                cust_name = str(res[6].encode('ascii','ignore').decode('ascii')) if res[6] != None else ''
                type = str(res[7].encode('ascii','ignore').decode('ascii')) if res[7] != None else ''
                warna = str(res[8].encode('ascii','ignore').decode('ascii')) if res[8] != None else ''
                qty = res[9]
                harga_jual = res[10]
                disc = res[11]
                harga_jual_excl_tax = res[12]           
                nett_sales = res[13]
                discount_cash_avg = res[14]
                discount_lain_avg = res[15]
                discount_program_avg = res[16]
                dpp = res[17]
                tax = res[18]
                total = res[19]
                categ_name = str(res[20].encode('ascii','ignore').decode('ascii')) if res[20] != None else ''
                categ2_name = str(res[21].encode('ascii','ignore').decode('ascii')) if res[21] != None else ''
                prod_series = str(res[22].encode('ascii','ignore').decode('ascii')) if res[22] != None else ''
                no_invoice = str(res[23].encode('ascii','ignore').decode('ascii')) if res[23] != None else '' 
                faktur_pajak = str(res[24].encode('ascii','ignore').decode('ascii')) if res[24] != None else ''
                soc_id = res[25]

                if soc_id > 0 :
                    qty = -qty
                    harga_jual = -harga_jual
                    disc = -disc
                    harga_jual_excl_tax = -harga_jual_excl_tax
                    nett_sales = -nett_sales
                    discount_cash_avg = -discount_cash_avg
                    discount_lain_avg = -discount_lain_avg
                    discount_program_avg = -discount_program_avg
                    dpp = -dpp
                    tax = -tax
                    total = -total

                writer.writerow([branch_code, branch_name, name, state, date_order,
                                     cust_code, cust_name, type, warna, qty, harga_jual,
                                     disc, harga_jual_excl_tax, nett_sales,
                                     discount_cash_avg, discount_lain_avg, discount_program_avg,
                                     dpp, tax, total, categ_name, categ2_name,
                                     prod_series, no_invoice, faktur_pajak,])
                
            csv_bytes = fp.getvalue()
            csv_bytes = csv_bytes.encode('utf-8')
            file_data_bytes_b64 = base64.b64encode(csv_bytes)
            file_data_str_b64 = file_data_bytes_b64.decode('utf-8')

            report_name = f"Report_Penjualan_MD_{self._get_default_date()}.csv"
            self.write({'file': file_data_str_b64, 'name': report_name})
            download_url = '/web/content/%s/%s/file?download=true' % (self._name, self.id)
    
            return {
                'type': 'ir.actions.act_url',
                'url': download_url,
                'target': 'new',
            }