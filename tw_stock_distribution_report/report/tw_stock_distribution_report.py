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
class TwStockDistributionReport(models.TransientModel):
    _name = "tw.stock.distribution.report"
    _description = "Report Stock Distribution"

    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now()
    
    # 8: fields
    def _get_company_ids(self):
        company_ids_user = self.env.user.company_ids
        company_ids = [b.id for b in company_ids_user]
        return company_ids

    name = fields.Char(string="Filename", readonly=True)
    options = fields.Selection(
        [
            ('sd_detail','Stock Distribution Detail'),
            ('sd_order',"Stock Distribution's Mutation Order")
        ],
        string="Options",
        required=True,
        default='sd_detail'
    )
    state = fields.Selection(
        [
            ('requested','Requested'),
            ('open','Open'),
            ('done','Done'),
            ('open_done','Open & Done'),
            ('open_done_cancel','Open, Done & Cancelled'),
            ('reject','Rejected'),
            ('all','All')
        ],
        "Stock Distribution's State",
        change_default=True
    )
    order_state = fields.Selection(
        [
            ('all','All'),
            ('draft','Draft'),
            ('confirm','In Progress'),
            ('done','Done'),
            ('cancel','Cancelled')
        ],
        "Order's State",
        change_default=True
    )
    trx_type = fields.Selection(
        [
            ('all','All'),
            ('sales','Sales')
        ],
        'Transaction Type'
    )
    division = fields.Selection(
        [
            ('Unit','Unit'),
            ('Sparepart','Sparepart')
        ],
        'Division'
    )
    start_date = fields.Date('Start Date',default=_get_default_date)
    end_date = fields.Date('End Date',default=_get_default_date)

    # 9: relation fields
    dealer_ids = fields.Many2many('res.partner', 'tw_stock_distribution_report_partner_rel', 'tw_stock_distribution_report', 'partner_id', 'Partners', copy=False, domain=[('category_id.name','in',['Dealer'])])
    company_ids = fields.Many2many('res.company', 'tw_stock_distribution_report_branch_rel', 'tw_stock_distribution_report', 'company_id', "Branch", copy=False)

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods
    def excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        start_date,end_date = self._get_date_range()
        if len(self.company_ids) == 0 :
            self.update({'company_ids': self._get_company_ids()})
        if self.options == 'sd_detail' :
            filename = 'Report Stock Distribution Detail'
            ress = self._print_excel_report_detail()
        else :
            filename = 'Report Stock Distribution Order'
            ress = self._print_excel_report_order()

        return self.env['web.report'].sudo().generate_report(filename,ress, data_summary_header=False, start_date=start_date, end_date=end_date)

    def _print_excel_report_detail(self):
        state = self.state
        division = self.division
        trx_type = self.trx_type
        start_date = self.start_date
        end_date = self.end_date
        company_ids = self.company_ids.ids
        dealer_ids = self.dealer_ids.ids
        state_str = ''
        division_str = 'All'
        trx_type_str = 'All'

        query = self._query_report_stock_distribution_detail(
            state=state,
            division=division,
            trx_type=trx_type,
            start_date=start_date,
            end_date=end_date,
            company_ids=company_ids,
            dealer_ids=dealer_ids,
            state_str=state_str,
            division_str=division_str,
            trx_type_str=trx_type_str,
        )

        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        return ress

    def _print_excel_report_order(self):

        state = self.state
        order_state = self.order_state
        division = self.division
        trx_type = self.trx_type
        start_date = self.start_date
        end_date = self.end_date
        company_ids = self.company_ids.ids
        dealer_ids = self.dealer_ids.ids
        state_str = ''
        order_state_str = 'All'
        division_str = 'All'
        trx_type_str = 'All'

        query_where = ""

        if state == 'requested' :
            query_where += " AND sd.state in ('confirm', 'waiting_for_approval', 'approved') "
            state_str = 'Requested'
        elif state == 'open' :
            query_where += " AND sd.state = 'open' "
            state_str = 'Open'
        elif state == 'done' :
            query_where += " AND sd.state in ('done', 'closed') "
            state_str = 'Done'
        elif state == 'open_done' :
            query_where += " AND sd.state in ('open', 'done', 'closed') "
            state_str = 'Open & Done'
        elif state == 'open_done_cancel' :
            query_where += " AND sd.state in ('open', 'done', 'closed', 'cancel') "
            state_str = 'Open, Done & Cancelled'
        elif state == 'reject' :
            query_where += " AND sd.state = 'reject' "
            state_str = 'Rejected'
        elif state == 'all' :
            query_where += ""
            state_str = 'All'

        if order_state == 'draft' :
            query_where += " AND so.state = 'draft' "
            order_state_str = 'Draft'
        elif order_state == 'confirm' :
            query_where += " AND so.state in ('progress', 'confirm') "
            order_state_str = 'In Progress'
        elif order_state == 'done' :
            query_where += " AND so.state = 'done' "
            order_state_str = 'Done'
        elif order_state == 'cancel' :
            query_where += " AND so.state in ('cancel', 'cancelled') "
            order_state_str = 'Cancelled'

        if division == 'Unit' :
            query_where += " AND sd.division = 'Unit' "
            division_str = 'Unit'
        elif division == 'Sparepart' :
            query_where += " AND sd.division = 'Sparepart' "
            division_str = 'Sparepart'

        if division == 'Sparepart':
            if start_date :
                query_where += " AND (so.create_date + interval '7 hours')::date >= '%s' " % start_date
                
            if end_date :
                query_where += " AND (so.create_date + interval '7 hours')::date <= '%s' " % end_date
        else:
            if start_date :
                query_where += " AND sd.date >= '%s' " % start_date
                
            if end_date :
                query_where += " AND sd.date <= '%s' " % end_date

        if company_ids :
            query_where += " AND b.id in %s " % str(tuple(company_ids)).replace(',)', ')')
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND b.id IN {str(tuple(branch)).replace(',)', ')')}"

        if dealer_ids :
            query_where += " AND dealer.id in %s " % str(tuple(dealer_ids)).replace(',)', ')')

        query = self._get_query_report_order(trx_type, order_state, query_where)        

        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        return ress

    def _get_query_report_order(self, trx_type, order_state, query_where):
        query = ""
        query_sales = ""
        if trx_type == 'sales' or trx_type == 'all' or trx_type == False :
            if order_state == 'confirm' :
                query_where += " AND (sol.product_uom_qty IS NOT NULL AND dist.qty IS NOT NULL AND sol.product_uom_qty != dist.qty) "
            query_sales = """
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
                , (so.date_order + interval '7 hours')::timestamp::date as order_date
                , so.state as order_state
                , prod_template.default_code as product
                , COALESCE(pav.code,'') as color
                , prod_cat.name as category
                , COALESCE(sol.product_uom_qty, 0) as qty
                , COALESCE(sol.price_unit, 0) as unit_price
                , COALESCE(sol.discount, 0) as discount
                , COALESCE(sol.product_uom_qty, 0)*COALESCE(sol.price_unit, 0) as est_amount
                , COALESCE(dist.qty, 0) as supplied_qty
                , COALESCE(dist.qty, 0)*COALESCE(sol.price_unit, 0) as est_supplied_amount
                , COALESCE(sol.product_uom_qty, 0)-COALESCE(dist.qty, 0) as outstanding_qty
                , COALESCE(sol.price_unit, 0)*(COALESCE(sol.product_uom_qty, 0)-COALESCE(dist.qty, 0))*(100-COALESCE(sol.discount, 0))/100 as est_outstanding_amount
                from tw_stock_distribution sd
                left join res_company b on sd.company_id = b.id
                --TODO: dealer_id tidak ada jadinya menggunakan requester_id apakah perlu penyesuaian?
                left join res_partner dealer on sd.requester_id = dealer.id
                left join tw_sale_order so on sd.id = so.stock_distribution_id
                left join tw_sale_order_line sol on so.id = sol.order_id
                left join product_product product on sol.product_id = product.id
                LEFT JOIN product_variant_combination vcom on vcom.product_product_id = product.id
                LEFT JOIN product_template_attribute_value ptav ON ptav.id = vcom.product_template_attribute_value_id
                LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id 
                left join product_template prod_template on product.product_tmpl_id = prod_template.id
                left join product_category prod_cat on prod_template.categ_id = prod_cat.id
                left join (select pick.origin, move.product_id, sum(move.product_qty) as qty
                from stock_picking pick
                inner join stock_move move on pick.id = move.picking_id
                where pick.state = 'done'
                group by pick.origin, move.product_id) dist on so.name = dist.origin and sol.product_id = dist.product_id
                where sd.requester_id IS NULL
                %s
                order by branch_code, dealer_code, date, sd.name, order_date, order_name)
            """ % (query_where)

        if trx_type == 'sales' :
            query = query_sales
        elif trx_type == 'all':
            query = query_sales

        return query

    def _query_report_stock_distribution_detail(self, **kwargs):
        state = kwargs['state'] if 'state' in kwargs else None
        division = kwargs['division'] if 'division' in kwargs else None
        trx_type = kwargs['trx_type'] if 'trx_type' in kwargs else None
        start_date = kwargs['start_date'] if 'start_date' in kwargs else None
        end_date = kwargs['end_date'] if 'end_date' in kwargs else None
        company_ids = kwargs['company_ids'] if 'company_ids' in kwargs else None
        dealer_ids = kwargs['dealer_ids'] if 'dealer_ids' in kwargs else None
        state_str = kwargs['state_str'] if 'state_str' in kwargs else ''
        division_str = kwargs['division_str'] if 'division_str' in kwargs else 'All'
        trx_type_str = kwargs['trx_type_str'] if 'trx_type_str' in kwargs else 'All'
        import ipdb; ipdb.set_trace()

        query_where = " WHERE 1=1 "

        if state == 'requested' :
            query_where += " AND sd.state in ('confirm', 'waiting_for_approval', 'approved') "
            state_str = 'Requested'
        elif state == 'open' :
            query_where += " AND sd.state = 'open' "
            state_str = 'Open'
        elif state == 'done' :
            query_where += " AND sd.state in ('done', 'closed') "
            state_str = 'Done'
        elif state == 'open_done' :
            query_where += " AND sd.state in ('open', 'done', 'closed') "
            state_str = 'Open & Done'
        elif state == 'open_done_cancel' :
            query_where += " AND sd.state in ('open', 'done', 'closed', 'cancel') "
            state_str = 'Open, Done & Cancelled'
        elif state == 'reject' :
            query_where += " AND sd.state = 'reject' "
            state_str = 'Rejected'
        elif state == 'all' :
            query_where += ""
            state_str = 'All'

        if division == 'Unit' :
            query_where += " AND sd.division = 'Unit' "
            division_str = 'Unit'
        elif division == 'Sparepart' :
            query_where += " AND sd.division = 'Sparepart' "
            division_str = 'Sparepart'

        if trx_type == 'mutation' :
            query_where += " AND sd.requester_id IS NOT NULL "
            trx_type_str = 'Mutation'
        elif trx_type == 'sales' :
            query_where += " AND sd.requester_id IS NULL "
            trx_type_str = 'Sales'

        if start_date :
            query_where += " AND sd.date >= '%s' " % start_date
            
        if end_date :
            query_where += " AND sd.date <= '%s' " % end_date

        if company_ids :
            query_where += " AND b.id in %s " % str(tuple(company_ids)).replace(',)', ')')
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND b.id IN {str(tuple(branch)).replace(',)', ')')}"

        if dealer_ids :
            query_where += " AND dealer.id in %s " % str(tuple(dealer_ids)).replace(',)', ')')

        query = """
            select b.code as branch_code
            , b.name as branch_name
            , dealer.code as dealer_code
            , dealer.name as dealer_name
            , CASE WHEN dealer.route_type = 'internal' THEN 'Mutation' ELSE 'Sales' END as transaction_type
            , sd.division
            , pot.name as tipe_po
            , sd.origin as no_p2p
            , sd.name as stock_distribution
            , sd.date
            , sd.state
            , sd.start_date
            , sd.end_date
            , sd.description
            , prod_template.default_code as product
            , COALESCE(pav.code,'') as color
            , prod_cat.name as category
            , COALESCE(sdl.price, 0) as unit_price
            , COALESCE(sdl.requested_qty,0) as requested_qty
            , COALESCE(sdl.price, 0)*COALESCE(sdl.requested_qty,0) as requested_amount
            , COALESCE(sdl.approved_qty, 0) as approved_qty
            , COALESCE(sdl.price, 0)*COALESCE(sdl.approved_qty, 0) approved_amount
            , COALESCE(sdl.qty, 0) as qty
            , COALESCE(sdl.price, 0)*COALESCE(sdl.qty, 0) as amount
            , COALESCE(sdl.supply_qty, 0) as supplied_qty
            , COALESCE(sdl.supply_qty, 0)*COALESCE(sdl.price, 0) as supplied_amount
            from tw_stock_distribution sd
            left join res_company b on sd.company_id = b.id
            left join tw_purchase_order_type pot on sd.purchase_order_type_id = pot.id
            --TODO: dealer_id tidak ada jadinya menggunakan requester_id apakah perlu penyesuaian?
            left join res_partner dealer on sd.requester_id = dealer.id
            left join tw_stock_distribution_line sdl on sd.id = sdl.stock_distribution_id
            left join product_product product on sdl.product_id = product.id
            LEFT JOIN product_variant_combination vcom on vcom.product_product_id = product.id
            LEFT JOIN product_template_attribute_value ptav ON ptav.id = vcom.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id 
            left join product_template prod_template on product.product_tmpl_id = prod_template.id
            left join product_category prod_cat on prod_template.categ_id = prod_cat.id

            %s

            order by b.code, sd.date, sd.id, sdl.id
        """ % (query_where)

        return query

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
    