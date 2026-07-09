from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning

class StockPickingReport(models.TransientModel):
    _name = "tw.stock.picking.report"
    _description = "Stock Picking Report"

    def _get_default_date(self):
        return datetime.now()

    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    picking_type = fields.Selection([
        ('all','All'),
        ('in','In'),
        ('out','Out'),
        ('incoming','Receipts'),
        ('outgoing','Delivery Orders'),
        ('internal','Internal Transfers'),
        ('interbranch_in','Interbranch Receipts'),
        ('interbranch_out','Interbranch Deliveries')
    ], string='Picking Type', default='all')

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)

    company_ids = fields.Many2many(comodel_name='res.company', relation='tw_stock_picking_report_company_rel',
                                  column1='stock_picking_id', column2='company_id', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)], store=True)
    categ_ids = fields.Many2many('product.category', 'tw_stock_picking_report_categ_rel', 'stock_picking_id','categ_id', 'Category', domain="[('parent_id', '!=', False)]")
    product_ids = fields.Many2many('product.product', 'tw_stock_picking_report_product_rel', 'stock_picking_id','product_id', 'Product')
    partner_ids = fields.Many2many('res.partner', 'tw_stock_picking_report_partner_rel', 'stock_picking_id','partner_id', 'Partner')

    def action_export_report(self,return_fp=False):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        query_where = "WHERE 1=1"
        if self.division == 'Unit':
            query_where += " AND pt.division = 'Unit' and sm.product_qty > 0 and sp.state != 'done' "
        else:
            query_where += " AND pt.division != 'Unit' and sm.product_qty > 0 and sp.state != 'done' "
            
        query_where += f" AND sp.division = '{self.division}'"
       
        if self.picking_type :
            if self.picking_type == 'all' :
                query_where += " AND spt.code in ('incoming','outgoing','interbranch_in','interbranch_out')"
            elif self.picking_type == 'in' :
                query_where += " AND spt.code in ('incoming','interbranch_in')"
            elif self.picking_type == 'out' :
                query_where += " AND spt.code in ('outgoing','interbranch_out')"
            elif self.picking_type == 'internal' :
                query_where += " AND spt.code = 'internal' AND sp.type = 'internal'"
            elif self.picking_type == 'interbranch_in' :
                query_where += " AND sp.mutation_order_id IS NOT NULL AND spt.code = 'incoming'"
            elif self.picking_type == 'interbranch_out' :
                query_where += " AND sp.mutation_order_id IS NOT NULL AND spt.code = 'outgoing'"
            else :
                query_where += f" AND spt.code = '{self.picking_type}'"
                
        if self.start_date :
            query_where += f" AND date(sp.create_date) >= '{self.start_date}'"

        if self.end_date :
            query_where += f" AND date(sp.create_date) <= '{self.end_date}'"

        if self.company_ids :
            company_ids = str(tuple([company.id for company in self.company_ids])).replace(',)', ')')
            query_where += f" AND sp.company_id IN {company_ids}"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND sp.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.product_ids :
            product_ids = str(tuple([prod.id for prod in self.product_ids])).replace(',)', ')')
            query_where += f" AND pp.id IN {product_ids}"

        if self.partner_ids :
            partner_ids = str(tuple([partner.id for partner in self.partner_ids])).replace(',)', ')')
            query_where += f" AND sp.partner_id IN {partner_ids}"

        if self.categ_ids :
            categ_ids = str(tuple([categ.id for categ in self.categ_ids])).replace(',)', ')')
            query_where += f" AND pc.id IN {categ_ids}"

        query = f"""
            SELECT DISTINCT 
                rc.code AS "Branch Code"
                , rc.name AS "Branch Name"
                , sp.division AS "Division"
                , spt.name->>'en_US' AS "Picking Type"
                , sp.name AS "Picking Name"
                , '' AS "Packing Name"
                , to_char(DATE(sp.date_done + INTERVAL '7 hours'), 'YYYY-MM-DD') AS "Packing Date"
                , rp.code AS "Partner Code"
                , rp.name AS "Partner Name"
                , '' AS "Ekspedisi Code"
                , '' AS "Ekspedisi Name"
                , pp.default_code AS "Product"
                , pav.code AS "Color"
                , sl.name AS "No. Engine"
                , sl.chassis_number AS "No. Chassis"
                , sl.production_year AS "Production Year"
                , COALESCE(sml.quantity, sm.product_qty) AS "Qty"
                , loc_src.name AS "Source Location"
                , loc_dest.name AS "Destination Location"
                , sp.state AS "State"
                , sp.origin AS "Source Document"
                , COALESCE(sp2.name,'') AS "Backorder"
                , sl.ship_list_number AS "SL AHM"
            FROM stock_picking sp 
            INNER JOIN stock_move sm on sp.id = sm.picking_id 
            LEFT JOIN stock_move_line sml on sm.id = sml.move_id 
            LEFT JOIN stock_lot sl on sml.lot_id = sl.id
            LEFT JOIN stock_picking_type spt on spt.id = sp.picking_type_id 
            LEFT JOIN res_company rc on sp.company_id = rc.id 
            LEFT JOIN res_partner rp on sp.partner_id = rp.id 
            LEFT JOIN stock_picking sp2 on sp.backorder_id = sp2.id
            LEFT JOIN product_product pp on sm.product_id = pp.id
            LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id
            LEFT JOIN product_category pc on pt.categ_id = pc.id
            LEFT JOIN product_variant_combination as pvc on pvc.product_product_id = pp.id
            LEFT JOIN product_template_attribute_value as ptav on ptav.id = pvc.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            LEFT JOIN stock_location loc_src on sm.location_id = loc_src.id 
            LEFT JOIN stock_location loc_dest on sm.location_dest_id = loc_dest.id
            {query_where}
            ORDER BY rc.code
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Report Stock Picking', result, return_fp=return_fp)


    