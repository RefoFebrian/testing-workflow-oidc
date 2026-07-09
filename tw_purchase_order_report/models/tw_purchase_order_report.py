# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date , timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwPurchaseOrderReport(models.TransientModel):
    _name = "tw.purchase.order.report"
    _description = "Purchase Report"

    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()
    
    # 8: fields
    name = fields.Char('Filename')
    options = fields.Selection([('pembelian','Pembelian')],'Options', required=True, default='pembelian')
    state = fields.Selection([('confirmed','Confirmed'), ('invoiced','Invoiced'), ('received','Received'), ('all','All')], 'State', required=True, default='confirmed')
    invoice_state = fields.Selection([('all','All'), ('to_invoice','To Invoice'), ('not_paid','Not Paid'), ('paid','Paid')], 'Invoice State', default='all')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default=lambda self: self.env.context.get('default_division'))
    start_date = fields.Date('Start Date', required=True, default=date.today())
    end_date = fields.Date('End Date', required=True, default=date.today())
    product_ids = fields.Many2many('product.product','tw_report_pembelian_product_rel','tw_report_pembelian_wizard_id', 'product_id', 'Products')
    company_ids = fields.Many2many('res.company','tw_report_pembelian_company_rel','tw_report_pembelian_wizard_id', 'company_id', "Branch", copy=False)
    partner_ids = fields.Many2many('res.partner','tw_report_pembelian_partner_rel','tw_report_pembelian_wizard_id', 'partner_id', 'Suppliers', copy=False)

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_generate_report(self,return_fp=False):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = f" WHERE po.state != 'draft' AND po.date between '{self.start_date}' AND '{self.end_date}' AND po.division = '{self.division}'"

        if self.company_ids:
            query_where += f" AND po.company_id IN {str(tuple([b.id for b in self.company_ids])).replace(',)', ')')}"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND po.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        
        if self.product_ids:
            query_where += f" AND pp.id IN {str(tuple([p.id for p in self.product_ids])).replace(',)', ')')}"
        
        if self.partner_ids:
            query_where += f" AND po.partner_id IN {str(tuple([p.id for p in self.partner_ids])).replace(',)', ')')}"
        
        if self.state == 'confirmed':
            query_where += " AND po.state in ('confirmed','open','done','purchase')"
        elif self.state == 'invoiced':
            query_where += " AND pol.qty_invoiced > 0 AND inv.qty > 0"
        elif self.state == 'received':
            query_where += " AND pol.qty_received > 0 AND inv.qty > 0"

        if self.invoice_state == 'all':
            query_where += " "
        elif self.invoice_state == 'to_invoice':
            query_where += " AND po.invoice_status = 'to invoice'"
        elif self.invoice_state == 'not_paid':
            query_where += " AND po.invoice_status in ('invoiced','no') AND inv.payment_state != 'Paid'"
        elif self.invoice_state == 'paid':
            query_where += " AND po.invoice_status in ('invoiced','no') AND inv.payment_state = 'Paid'"

        query = f"""
            SELECT 
                rc.name as "Branch"
                ,rc.code as "Branch Code"
                ,rp.name as "Supplier"
                ,rp.code as "Supplier Code"
                ,po.division
                ,po.name as "Purchase Order"
                ,po.date as "Purchase Order Date"
                ,po.state as "State"
                ,pt.name->>'en_US' as "Product Name"
                ,pp.default_code as "Product Code"
                ,att."name" as "Attribute"
                ,att."code" as "Attribute Code"
                ,pc.name as "Category"
                ,pol.product_qty as "Ordered Quantity"
                ,pol.qty_received as "Received Quantity"
                ,pol.qty_invoiced as  "Invoiced Quantity"
                ,coalesce(pol.consolidated_qty,0) as  "Consolidated Quantity"
                ,ROUND((pol.price_subtotal / pol.product_qty),2) as "PO Unit Price (Per Unit)"
                ,ROUND(pol.price_subtotal,2)  as "PO Subtotal Price"
                ,ROUND(pol.price_total - pol.price_subtotal,2) as "PO Tax Price"
                ,ROUND(pol.price_total,2) as "PO Total Price"
                ,inv.name as "Invoice Name"
                ,inv.payment_state as "Invoice State"
                ,inv.payment_reference as "Invoice Reference"
                ,coalesce((inv.subtotal / inv.qty),0) as "Invoice Unit Price"
                ,coalesce(inv.discount,0) as "Invoice Discount "
                ,coalesce(inv.qty,0) as "Invoice Qty"
                ,coalesce(inv.subtotal,0) as "Invoice Subtotal"
                ,coalesce(inv.discount_cash,0) as "Discount Cash"
                ,coalesce(inv.discount_program,0) as "Discount Program"
                ,coalesce(inv.discount_other,0) as "Discount Other"
                ,coalesce(inv.total_dpp,0) as "Total DPP"
                ,coalesce(inv.total_tax,0) as "Total Tax"
                ,coalesce(inv.total_hutang,0) as "Total Hutang"
            FROM purchase_order po
                JOIN purchase_order_line pol on pol.order_id = po.id
                JOIN res_partner rp on rp.id = po.partner_id 
                JOIN res_company rc on rc.id = po.company_id
                JOIN res_partner rpc on rpc.id = rc.partner_id 
                JOIN product_product pp on pp.id = pol.product_id
                JOIN product_template pt on pt.id = pp.product_tmpl_id
                JOIN product_category pc on pc.id = pt.categ_id 
                LEFT JOIN LATERAL(
                	select pvc.product_product_id, string_agg(pav.name->>rpc.lang,',') as name,string_agg(pav.code,',') as code
                	from product_variant_combination as pvc 
		            LEFT JOIN product_template_attribute_value as ptav on ptav.id = pvc.product_template_attribute_value_id
		            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
		            where pvc.product_product_id = pp.id
		            group by pvc.product_product_id
                ) as att on att.product_product_id = pp.id
                LEFT JOIN LATERAL (
                    SELECT 
                        purchase_line_id,
                        payment_reference,
                        payment_state,
                        price_unit,
                        name,
                        discount,
                        subtotal,
                        discount_cash,
                        discount_program,
                        discount_other,
                        qty,
                        (subtotal - (discount_cash + discount_program + discount_other)) as total_dpp,
                        (raw_tax - ((discount_cash + discount_program + discount_other) * raw_tax / NULLIF(subtotal, 0))) as total_tax,
                        (raw_total - ((discount_cash + discount_program + discount_other) * raw_total / NULLIF(subtotal, 0))) as total_hutang
                    FROM (
                        SELECT aml.purchase_line_id
                            ,am.payment_reference
                            ,string_agg(INITCAP(coalesce(replace(am.payment_state,'_',' ') ,'-')),',') as payment_state
                            ,max(aml.price_unit) price_unit,string_agg(am.name,',') as name
                            ,sum(aml.discount_amount_currency) as discount
                            ,sum(aml.price_subtotal) subtotal
                            ,sum(aml.price_total - aml.price_subtotal) raw_tax
                            ,sum(aml.price_total) raw_total
                            ,COALESCE(AVG(dc.price_unit * -1) / NULLIF(COALESCE((SELECT SUM(quantity) FROM account_move_line WHERE move_id = am.id AND display_type = 'product' AND price_unit > 0), 0), 0) * SUM(aml.quantity), 0) as discount_cash
                            ,COALESCE(AVG(dp.price_unit * -1) / NULLIF(COALESCE((SELECT SUM(quantity) FROM account_move_line WHERE move_id = am.id AND display_type = 'product' AND price_unit > 0), 0), 0) * SUM(aml.quantity), 0) as discount_program
                            ,COALESCE(AVG(dl.price_unit * -1) / NULLIF(COALESCE((SELECT SUM(quantity) FROM account_move_line WHERE move_id = am.id AND display_type = 'product' AND price_unit > 0), 0), 0) * SUM(aml.quantity), 0) as discount_other
                            ,sum(aml.quantity) as qty 
                        FROM account_move_line aml
                        LEFT JOIN account_move am on am.id = aml.move_id
                        LEFT JOIN account_move_line dc on dc.move_id = am.id and dc.name = 'Discount Cash'
                        LEFT JOIN account_move_line dp on dp.move_id = am.id and dp.name = 'Discount Program'
                        LEFT JOIN account_move_line dl on dl.move_id = am.id and dl.name = 'Discount Other'
                        WHERE aml.purchase_line_id = pol.id
                        GROUP by aml.purchase_line_id,am.id,am.payment_reference
                    ) sub_inv
                ) as inv on inv.purchase_line_id = pol.id
            {query_where}
            ORDER BY rc.code,po.name,pt.id
        """

        self._cr.execute(query)
        ress =  self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Report Purchase Order',ress,capitalize=False,return_fp=return_fp)

    # 14: private methods

    

    