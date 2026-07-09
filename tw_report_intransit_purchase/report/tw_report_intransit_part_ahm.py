# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, tools
from odoo import api, fields, models

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class TwWorkOrderReportIntransitPurchaseInherit(models.TransientModel):
    _inherit = "tw.report.intransit.purchase"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _print_excel_report_intransit_part_ahm(self):
        branch_ids = self.company_ids.ids
        start_date = self.start_date
        end_date = self.end_date  
        query_where = ""
        if start_date:
            query_where += " and sp.date >= '%s' " % start_date
        if end_date:
            query_where += " and sp.date <= '%s' " % end_date
        query = f"""
            select b.code as branch_code
            , b.name as branch_name
            , sp.division as division
            , rp.code as supplier_code
            , rp.name as supplier_name
            , sp.origin as no_ps
            , sp.name as no_picking
            , (sm.create_date + interval '7 hours')::timestamp::date as upload_date
            , pt.name->>'en_US' as product_name
            , sm.product_uom_qty as product_qty
            , sm.price_unit / (1 + COALESCE(tax.amount,0)) as hpp
            , sm.price_unit / (1 + COALESCE(tax.amount,0)) * sm.product_uom_qty as subtotal
            from stock_picking sp
            inner join stock_move sm on sp.id = sm.picking_id
            left join res_company b on sp.company_id = b.id
            left join res_partner rp on rp.id = sp.partner_id
            left join stock_picking_type spt on sp.picking_type_id = spt.id 
            left join product_product p on sm.product_id = p.id
            LEFT JOIN product_template pt on pt.id = p.product_tmpl_id
            LEFT JOIN LATERAL(
                SELECT ptr.prod_id, tax.amount
                FROM product_supplier_taxes_rel ptr
                INNER JOIN account_tax tax ON tax.id = ptr.tax_id
                WHERE tax.type_tax_use = 'purchase'
                AND ptr.prod_id = p.id
                LIMIT 1
            ) tax ON tax.prod_id = p.id
            where spt.code = 'incoming'
            and sp.state = 'assigned'
            and rp.code = 'AHM'
            and sp.division = 'Sparepart'
            and sp.company_id in {(str(tuple(branch_ids)).replace(',)', ')'))}
            {query_where}
            order by b.code, rp.code, sp.origin, pt.name->>'en_US', sm.product_uom_qty desc
            """

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        return ress