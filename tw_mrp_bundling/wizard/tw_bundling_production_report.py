# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwBundlingProductionReport(models.TransientModel):
    _name = "tw.bundling.production.report"
    _description = "Bundling Production Report"

    # 7: defaults methods
    def _get_default_date(self): 
        return fields.Date.today()
    
    # 8: fields
    start_date = fields.Date('Start Date', default=_get_default_date, required=True)
    end_date = fields.Date('End Date', default=_get_default_date, required=True)
    
    state_filter = fields.Selection([
        ('progress_done', 'Progress & Done'),
        ('done', 'Done')
    ], string='State Filter', default='progress_done', required=True)
    
    division_filter = fields.Selection([
        ('all', 'All'),
        ('unit', 'Unit Only'),
        ('non_unit', 'Non-Unit Only')
    ], string='Product Type', default='all', required=True)

    # 9: relation fields
    company_ids = fields.Many2many('res.company', string='Branch')

    # 13: Action Methods
    def action_print_excel(self):
        self.ensure_one()
        # Check date range limit using web.report's helper
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        
        query = self._get_report_query()
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        
        if not ress:
            raise Warning(_("Data tidak ada..."))

        filename = 'Report Bundling Production'
        start_date = self.start_date.strftime('%Y-%m-%d')
        end_date = self.end_date.strftime('%Y-%m-%d')

        return self.env['web.report'].sudo().generate_report(
            filename,
            ress,
            data_summary_header=False,
            start_date=start_date,
            end_date=end_date,
            show_total_footer=False
        )

    def _get_report_query(self):
        query_where = " WHERE mrp.order_type = 'bundling' "
        
        # Date Filter
        if self.start_date:
            query_where += " AND mrp.date >= '%s' " % self.start_date
        if self.end_date:
            query_where += " AND mrp.date <= '%s' " % self.end_date
            
        # State Filter
        if self.state_filter == 'done':
            query_where += " AND mrp.state = 'done' "
        elif self.state_filter == 'progress_done':
            query_where += " AND mrp.state IN ('confirmed', 'progress', 'to_close', 'done') "
            
        # Division / Product Type Filter
        if self.division_filter == 'unit':
            query_where += " AND pt_comp.division = 'Unit' "
        elif self.division_filter == 'non_unit':
            query_where += " AND (pt_comp.division != 'Unit' OR pt_comp.division IS NULL) "
            
        # Branch/Company Filter
        if self.company_ids:
            query_where += " AND mrp.company_id IN %s " % str(tuple(self.company_ids.ids)).replace(',)', ')')
        else:
            # Fallback to user allowed companies
            allowed_companies = self.env.context.get('allowed_company_ids', self.env.company.ids)
            query_where += " AND mrp.company_id IN %s " % str(tuple(allowed_companies)).replace(',)', ')')

        query = """
            SELECT 
                comp.code AS "Branch Code",
                comp.name AS "Branch Name",
                mrp.date AS "Date",
                mrp.name AS "Bundling",
                initcap(mrp.state) as "State",
                prod_fin.default_code AS "Kode Produk Bundling",
                pt_fin.name ->>'en_US' AS "Produk Bundling",
                pt_comp.division,
                prod_comp.default_code AS "Component Product Code",
                pt_comp.name  ->>'en_US' AS "Component Product",
                COALESCE(sml.quantity, sm.product_uom_qty) AS "Component Qty",
                COALESCE(lot_comp.name, '') AS "Component Lot/Serial"
            FROM mrp_production mrp
            LEFT JOIN res_company comp ON mrp.company_id = comp.id
            LEFT JOIN product_product prod_fin ON mrp.product_id = prod_fin.id
            LEFT JOIN product_template pt_fin ON prod_fin.product_tmpl_id = pt_fin.id
            LEFT JOIN stock_move sm ON sm.raw_material_production_id = mrp.id
            LEFT JOIN stock_move_line sml ON sml.move_id = sm.id
            LEFT JOIN product_product prod_comp ON COALESCE(sml.product_id, sm.product_id) = prod_comp.id
            LEFT JOIN product_template pt_comp ON prod_comp.product_tmpl_id = pt_comp.id
            LEFT JOIN stock_lot lot_comp ON sml.lot_id = lot_comp.id
            %s
            ORDER BY comp.id, mrp.id, prod_comp.default_code
        """ % query_where

        return query
