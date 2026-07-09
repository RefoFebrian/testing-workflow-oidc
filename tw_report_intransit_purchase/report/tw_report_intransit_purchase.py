# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib


# 3:  imports of odoo
from odoo import models, fields, tools
from odoo import api, fields, models

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class TwWorkOrderReportIntransitPurchase(models.TransientModel):
    _name = "tw.report.intransit.purchase"
    _description = "Work Order Report Purchase"

    # 7: defaults methods
        
    def _get_company_ids(self):
        company_ids_user = self.env.user.company_ids
        company_ids = [b.id for b in company_ids_user]
        return company_ids

    def _set_domain_company_ids(self):
        return [('id','in',self.env.user.company_ids.ids)]

    # 8: fields
    options = fields.Selection([
        ('detail','Detail per Product'),
        ('ahm-part','Intransit Sparepart AHM')
    ], 'Options')
    division_showroom = fields.Selection(string='Division Showroom', selection=lambda self: self.env['tw.selection'].get_division_options_list(['Unit','Umum']), default='Unit')
    division_workshop = fields.Selection(string='Division Workshop', selection=lambda self: self.env['tw.selection'].get_division_options_list(['Sparepart']), default='Sparepart')
    start_date = fields.Date('Start Date', default=fields.Date.today)
    end_date = fields.Date('End Date', default=fields.Date.today)

    # 9: relation fields
    company_ids = fields.Many2many('res.company', 'tw_report_intransit_beli_branch_rel', 'tw_report_intransit_beli',
                                    'company_id', 'Branch', copy=False, domain=_set_domain_company_ids)
    partner_ids = fields.Many2many('res.partner', 'tw_report_intransit_beli_partner_rel', 'tw_report_intransit_beli',
                                    'partner_id', 'Partner', copy=False)      

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def excel_report(self):
        start_date = self.start_date
        end_date = self.end_date

        if len(self.company_ids) == 0:
            self.company_ids = self._get_company_ids()

        if self.options == 'ahm-part':
            filename = 'Report Intransit Part AHM'
            ress = self._print_excel_report_intransit_part_ahm()
        else :
            filename = 'Report Intransit Beli'
            ress = self._print_excel_report_detail()
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self.env['web.report'].sudo().generate_report(filename,ress, data_summary_header=False, start_date=start_date, end_date=end_date)

    def _print_excel_report_detail(self):
        branch_ids = self.company_ids.ids
        partner_ids = self.partner_ids.ids
        division = ''
        if self._context.get('is_showroom',False):
            division = self.division_showroom
        elif self._context.get('is_workshop',False):
            division = self.division_workshop
        start_date = self.start_date
        end_date = self.end_date          
        
        query = """
            select DISTINCT ON (ail.id) b.code as branch
            , ai.name as number
            , ai.division as division
            , ai.invoice_date as date_invoice
            , partner.code as partner_code
            , partner.name as partner_name
            , ai.supplier_invoice_number as supplier_invoice_number
            , ai.invoice_date as document_date
            , ai.invoice_date_due as date_due
            , pt.name->>'en_US'as product_code
            , ail.name as product_name
            , ail.quantity as quantity
            , ail.price_unit as price_unit
            , ail.price_unit / (1 + COALESCE(tax.amount,0)) as nett_sales
            , ail.discount
            , ail.discount_amount_currency as discount_amount
            , ail.price_subtotal / NULLIF(ail.quantity, 0) AS dpp
            , ail.price_subtotal
            , ail.consolidated_qty
            , (ail.price_subtotal / NULLIF(ail.quantity, 0)) * (ail.quantity - ail.consolidated_qty) AS stock_intransit
            , ai.number_faktur_pajak
            , ai.date_faktur_pajak
            FROM account_move ai
            INNER JOIN account_move_line ail on ai.id = ail.move_id
            LEFT JOIN purchase_order_line pol on pol.id = ail.purchase_line_id
            LEFT JOIN account_move_line_account_tax_rel as amlatr on amlatr.account_move_line_id = ail.id
            LEFT JOIN account_tax as tax on tax.id = amlatr.account_tax_id
            INNER JOIN res_company b on b.id = ai.company_id
            LEFT JOIN res_partner partner on partner.id = ai.partner_id
            LEFT JOIN product_product prod on prod.id = ail.product_id
            LEFT JOIN product_template pt on pt.id = prod.product_tmpl_id
        """
        query_where = """ 
            where ai.division in ('Unit', 'Sparepart')
            and ai.state in ('draft','posted')
            and ai.payment_state != 'paid'
            and ai.move_type = 'in_invoice'
            and ail.purchase_line_id NOTNULL 
            and pol.product_qty != ail.consolidated_qty
        """
                        
        if branch_ids :
            query_where += " and b.id in %s " % str(tuple(branch_ids)).replace(',)', ')')  
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND b.id IN {str(tuple(branch)).replace(',)', ')')}"             
        if partner_ids :
            query_where += " and partner.id  in %s " % str(tuple(partner_ids)).replace(',)', ')')
        if division :
            query_where += " and ai.division = '%s' " % division                             
        if start_date :
            query_where += " and ai.invoice_date >= '%s' " % start_date
        if end_date :
            query_where += " and ai.invoice_date <= '%s' " % end_date 
                   
        query_order = " order by ail.id, b.code, ai.invoice_date, ai.name "
        
        self.env.cr.execute(query+query_where+query_order)
        ress = self.env.cr.dictfetchall()
        return ress