# 1: imports of python lib
from datetime import datetime, timedelta

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError


# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwReportReturnPembelian(models.TransientModel):
    _name = "tw.report.return.pembelian"
    _description = "Report Return Pembelian"

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return fields.Date.context_today(self)

    # 8: fields
    division = fields.Selection([('Sparepart', 'Sparepart'), ('Unit', 'Unit'), ('Umum', 'Umum')], string='Division')
    state = fields.Selection([('draft', 'Draft'), ('sale', 'Done')], string='State', default='sale')
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)

    # 9: relation fields
    company_ids = fields.Many2many('res.company', string="Branch")
    partner_ids = fields.Many2many('res.partner', string='Partners', domain=[('category_id.name', 'in', ['General Supplier', 'Supplier', 'Customer'])])

    # 10: constraints & sql constraints
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise UserError(_('End Date harus lebih besar dari Start Date.'))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def _get_where_clause(self):
        query_where = "WHERE 1=1"
        if self.division:
            query_where += f" AND purchase_return.division = '{self.division}'"
        if self.start_date:
            query_where += f" AND purchase_return.date_return::date >= '{self.start_date}'"
        if self.end_date:
            query_where += f" AND purchase_return.date_return::date <= '{self.end_date}'"
        if self.state:
            query_where += f" AND purchase_return.state = '{self.state}'"
        if self.company_ids:
            query_where += f" AND purchase_return.company_id IN ({', '.join(str(i) for i in self.company_ids.ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND purchase_return.company_id IN {str(tuple(branch)).replace(',)', ')')}"
        if self.partner_ids:
            query_where += f" AND purchase_return.partner_id IN ({', '.join(str(i) for i in self.partner_ids.ids)})"

        return query_where

    def excel_report(self):
        self.ensure_one()

        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = self._get_where_clause()

        query = f"""
            SELECT 
                company.code as "Branch Code",
                company.name as "Branch Name",
                partner.name as "Supplier",
                partner.code as "Kode Supplier",
                purchase_return.division as "Division",
                move_origin.invoice_origin as "Origin",
                move_origin.name as "Number",
                purchase_return.name as "Invoice Number",
                purchase_return.date_return as "Date",
                (CASE WHEN purchase_return.state = 'sale' THEN 'Done' ELSE INITCAP(purchase_return.state) END) as "State",
                product_tmpl.default_code as "Type",
                COALESCE(attr_val.code, '') as "Warna",
                (CASE WHEN product_categ.name::text LIKE '{{%%}}' THEN (product_categ.name::text)::jsonb->>branch_partner.lang ELSE product_categ.name::text END) as "Product Category",
                return_line.product_uom_qty as "Quantity",
                COALESCE(gen_move_line.consolidated_qty, 0) as "Consolidated Qty",
                (return_line.product_uom_qty - COALESCE(gen_move_line.consolidated_qty, 0)) as "Unconsolidated Qty",
                return_line.price_unit as "Price Unit",
                COALESCE(gen_move_line.discount, 0) as "Discount 1 (%)",
                0 as "Discount 2 (Rp)",
                (CASE WHEN return_line.product_uom_qty != 0 THEN return_line.price_subtotal / return_line.product_uom_qty ELSE 0 END) as "Sales (Per Unit)",
                return_line.price_subtotal as "Total Sales",
                COALESCE((COALESCE(disc_data.discount_cash, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0) as "Discount Cash (Avg)",
                COALESCE((COALESCE(disc_data.discount_program, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0) as "Discount Program (Avg)",
                COALESCE((COALESCE(disc_data.discount_lain, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0) as "Discount Lain (Avg)",
                (return_line.price_subtotal - 
                 COALESCE((COALESCE(disc_data.discount_cash, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0) - 
                 COALESCE((COALESCE(disc_data.discount_program, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0) - 
                 COALESCE((COALESCE(disc_data.discount_lain, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0)
                ) as "Total DPP",
                ((return_line.price_subtotal - 
                 COALESCE((COALESCE(disc_data.discount_cash, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0) - 
                 COALESCE((COALESCE(disc_data.discount_program, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0) - 
                 COALESCE((COALESCE(disc_data.discount_lain, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0)
                ) * CASE WHEN return_line.price_subtotal != 0 THEN return_line.price_tax / return_line.price_subtotal ELSE 0 END) as "Total PPN",
                ((return_line.price_subtotal - 
                 COALESCE((COALESCE(disc_data.discount_cash, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0) - 
                 COALESCE((COALESCE(disc_data.discount_program, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0) - 
                 COALESCE((COALESCE(disc_data.discount_lain, 0) / NULLIF(disc_data.total_qty, 0) * return_line.product_uom_qty), 0)
                ) * (1 + CASE WHEN return_line.price_subtotal != 0 THEN return_line.price_tax / return_line.price_subtotal ELSE 0 END)) as "Total Hutang"
            FROM tw_purchase_return purchase_return
            LEFT JOIN res_company company ON purchase_return.company_id = company.id
            LEFT JOIN res_partner branch_partner ON branch_partner.id = company.partner_id
            LEFT JOIN res_partner partner ON purchase_return.partner_id = partner.id
            LEFT JOIN account_move move_origin ON purchase_return.invoice_id = move_origin.id
            LEFT JOIN tw_purchase_return_line return_line ON purchase_return.id = return_line.order_id
            LEFT JOIN product_product product ON return_line.product_id = product.id
            LEFT JOIN product_template product_tmpl ON product.product_tmpl_id = product_tmpl.id
            LEFT JOIN product_category product_categ ON product_tmpl.categ_id = product_categ.id
            LEFT JOIN product_variant_combination prod_var_combo ON product.id = prod_var_combo.product_product_id
            LEFT JOIN product_template_attribute_value tmpl_attr_val ON tmpl_attr_val.id = prod_var_combo.product_template_attribute_value_id
            LEFT JOIN product_attribute_value attr_val ON attr_val.id = tmpl_attr_val.product_attribute_value_id
            LEFT JOIN tw_purchase_return_line_invoice_rel rel ON return_line.id = rel.order_line_id
            LEFT JOIN account_move_line gen_move_line ON rel.invoice_line_id = gen_move_line.id
            LEFT JOIN account_move gen_move ON gen_move_line.move_id = gen_move.id
            LEFT JOIN (
                SELECT 
                    m.id as move_id,
                    SUM(l.quantity) as total_qty,
                    SUM(CASE WHEN d.name = 'Discount Cash' THEN amd.amount ELSE 0 END) as discount_cash,
                    SUM(CASE WHEN d.name = 'Discount Program' THEN amd.amount ELSE 0 END) as discount_program,
                    SUM(CASE WHEN d.name = 'Discount Other' THEN amd.amount ELSE 0 END) as discount_lain
                FROM account_move m
                JOIN account_move_line l ON m.id = l.move_id
                LEFT JOIN account_move_discount amd ON m.id = amd.move_id
                LEFT JOIN tw_account_discount d ON amd.discount_id = d.id
                WHERE m.move_type = 'out_invoice' 
                AND l.product_id IS NOT NULL
                GROUP BY m.id
            ) disc_data ON gen_move.id = disc_data.move_id
            {query_where}
            ORDER BY company.code, purchase_return.name, purchase_return.date_return
        """

        self.env.cr.execute(query)
        data = self.env.cr.dictfetchall()
        report_name = 'Report Retur Pembelian'

        return self.env['web.report'].generate_report(report_name=report_name, data=data, start_date=self.start_date, end_date=self.end_date, header=True, numbering=True, show_total_footer=True)
    