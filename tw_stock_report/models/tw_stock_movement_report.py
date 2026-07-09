from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning

class StockMovementReport(models.TransientModel):
    _name = "tw.stock.movement.report"
    _description = "Stock Movement Report"

    def _get_default_date(self):
        return datetime.now()

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    options = fields.Selection([
        ('detail_movement','Detail Movement'), 
        ('outstanding','Outstanding Movement')
    ], string='Options', default='outstanding')
    picking_type = fields.Selection([
        ('all','All'),
        ('in','In'),
        ('out','Out'),
        ('incoming','Receipts'),
        ('outgoing','Delivery Orders'),
        ('internal','Internal Transfers'),
        ('interbranch_in','Interbranch Receipts'),
        ('interbranch_out','Interbranch Deliveries'),
    ], string='Picking Type', default='all')

    company_ids = fields.Many2many(comodel_name='res.company', relation='tw_stock_movement_report_company_rel',
                                  column1='stock_movement_id', column2='company_id', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)], store=True)
    categ_ids = fields.Many2many('product.category', 'tw_stock_movement_report_categ_rel', 'stock_movement_id','categ_id', 'Category', domain="[('parent_id', '!=', False)]")
    product_ids = fields.Many2many('product.product', 'tw_stock_movement_report_product_rel', 'stock_movement_id','product_id', 'Product')
    partner_ids = fields.Many2many('res.partner', 'tw_stock_movement_report_partner_rel', 'stock_movement_id','partner_id', 'Partner')

    def _get_base_fields(self, include_expedition=False, include_packing=False, include_mutation=False):
        """Base fields for all queries"""
        expedition_code = "expedition.code as expedition_code" if include_expedition else "'' as expedition_code"
        expedition_name = "expedition.name as expedition_name" if include_expedition else "'' as expedition_name"
        packing_name = "spb.name as packing_number" if include_packing else "'' as packing_number"
        mutation_name = "tsd.origin as mutation_number" if include_mutation else "'' as mutation_number"

        fields = [
            "company.code as branch_code",
            "company.name as branch_name",
            "picking.division",
            "spt.name->>'en_US' as picking_type",
            "picking.name as picking_number",
            packing_name,
            "date(picking.date + interval '7 hours') as movement_date",
            "partner.code as partner_code",
            "partner.name as partner_name",
            expedition_code,
            expedition_name,
            "prod_tmpl.default_code as product_code",
            "COALESCE(prod_tmpl.name->>'en_US', prod_tmpl.description->>'en_US') as product_name",
            "prod_categ.name as category_name",
            "attr_value.code as color_code",
            "COALESCE(lot.name, move_line.lot_name) as engine_number",
            "COALESCE(lot.chassis_number, move_line.chassis_number) as chassis_number",
            "COALESCE(lot.production_year, move_line.production_year) as production_year",
            "COALESCE(move_line.quantity, sm.product_qty) as qty",
            "sloc_src.name as source_location",
            "sloc_dest.name as destination_location",
            "picking.state as picking_state",
            "picking.origin as source_document",
            "COALESCE(backorder.name, '') as backorder",
            "lot.ship_list_number as shipping_list_ahm",
            "date(picking.validate_date + interval '7 hours') as receipt_date",
            "employee.name as validate_user",
            "move.name as invoice_receipt",
            mutation_name
        ]
            
        return ",\n ".join(fields)
                
    def _get_common_joins(self):
        """Common JOIN clauses for all queries"""
        return """
            FROM stock_picking picking
            LEFT JOIN stock_move sm ON picking.id = sm.picking_id
            LEFT JOIN stock_move_line move_line ON move_line.move_id = sm.id
            LEFT JOIN stock_picking_type spt ON spt.id = picking.picking_type_id
            LEFT JOIN stock_picking_stock_picking_batch_rel rel
			    ON rel.stock_picking_id = picking.id
			LEFT JOIN stock_picking_batch spb
			    ON spb.id = rel.stock_picking_batch_id
            LEFT JOIN res_company company ON company.id = picking.company_id
            LEFT JOIN res_partner partner ON partner.id = picking.partner_id
            LEFT JOIN product_product prod ON prod.id = sm.product_id
            LEFT JOIN product_template prod_tmpl ON prod_tmpl.id = prod.product_tmpl_id
            LEFT JOIN product_variant_combination variant ON prod.id = variant.product_product_id
            LEFT JOIN product_template_attribute_value attr ON variant.product_template_attribute_value_id = attr.id
            LEFT JOIN product_attribute_value attr_value ON attr.product_attribute_value_id = attr_value.id
            LEFT JOIN product_category prod_categ ON prod_tmpl.categ_id = prod_categ.id
            LEFT JOIN stock_lot lot ON lot.id = move_line.lot_id
            LEFT JOIN account_move move ON move.id = lot.supplier_invoice_id
            LEFT JOIN stock_picking backorder ON backorder.backorder_id = picking.id
            LEFT JOIN stock_location sloc_src ON sloc_src.id = move_line.location_id OR sloc_src.id = sm.location_id
            LEFT JOIN stock_location sloc_dest ON sloc_dest.id = move_line.location_dest_id OR sloc_dest.id = sm.location_dest_id
            LEFT JOIN res_users ru ON ru.id = picking.validate_uid
            LEFT JOIN resource_resource resource ON resource.user_id = ru.id
            LEFT JOIN hr_employee employee ON employee.resource_id = resource.id
            LEFT JOIN tw_mutation_order tmo ON tmo.name = picking.origin
            LEFT JOIN tw_stock_distribution tsd ON tsd.id = tmo.stock_distribution_id 
        """
        
    def _get_expedition_joins(self):
        """Additional JOINs for expedition data"""
        return """
            LEFT JOIN tw_stock_inbound inbound ON inbound.id = picking.stock_inbound_id
            LEFT JOIN res_partner expedition ON expedition.id = inbound.expedition_id
        """
        
    def _get_sale_order_joins(self):
        """Additional JOIN for sale order data"""
        return """
            JOIN tw_dealer_sale_order dso ON dso.name = picking.origin
        """

    def _get_query_conditions(self, include_expedition=False, include_sale_order=False):
        """Common query conditions"""
        conditions = []
        if include_expedition:
            conditions.append("""
                LEFT JOIN tw_stock_inbound inbound ON inbound.id = picking.stock_inbound_id
                LEFT JOIN res_partner expedition ON expedition.id = inbound.expedition_id
            """)
        if include_sale_order:
            conditions.append("JOIN tw_dealer_sale_order dso ON dso.name = picking.origin")
        return conditions

    def get_query_detail_movement_internal(self):
        query = f"""
            SELECT 
                {self._get_base_fields(include_expedition=False,include_packing=False,include_mutation=True)}
            {self._get_common_joins()}
            WHERE sm.product_qty > 0
            AND picking.state = 'done'
        """
        return query

    def get_query_detail_movement(self):
        query = f"""
            SELECT 
                {self._get_base_fields(include_expedition=True,include_packing=True,include_mutation=True)}
            {self._get_common_joins()}
            {self._get_expedition_joins()}
            WHERE sm.product_qty > 0
            AND picking.state = 'done'
        """
        return query

    def get_query_outstanding_movement(self):
        query = f"""
            SELECT 
                {self._get_base_fields(include_expedition=False,include_packing=False,include_mutation=True)}
            {self._get_common_joins()}
            WHERE sm.product_qty > 0
            AND picking.state NOT IN ('draft', 'cancel', 'done')
        """
        return query

    def get_query_detail_stock_out_movement(self):
        query = f"""
            SELECT 
                {self._get_base_fields(include_expedition=True,include_packing=True,include_mutation=False)}
            {self._get_common_joins()}
            {self._get_expedition_joins()}
            {self._get_sale_order_joins()}
            WHERE 1=1
        """
        return query

    def _get_query_filters(self):
        """Generate WHERE conditions based on filters"""
        filters = []
        
        if self.picking_type != 'all':
            if self.picking_type == 'in':
                filters.append(f"spt.code = 'incoming'")
            elif self.picking_type == 'out':
                filters.append(f"spt.code = 'outgoing'")
            elif self.picking_type == 'internal':
                filters.append(f"spt.code = 'internal'")
            elif self.picking_type == 'incoming':
                filters.append(f"spt.code = 'incoming'")
                filters.append(f"picking.mutation_order_id IS NULL")
            elif self.picking_type == 'outgoing':
                filters.append(f"spt.code = 'outgoing'")
                filters.append(f"picking.mutation_order_id IS NULL")
            elif self.picking_type == 'interbranch_in':
                filters.append(f"spt.code = 'incoming'")
                filters.append(f"picking.mutation_order_id IS NOT NULL")
            elif self.picking_type == 'interbranch_out':
                filters.append(f"spt.code = 'outgoing'")
                filters.append(f"picking.mutation_order_id IS NOT NULL")
            else:
                filters.append(f"spt.code = '{self.picking_type}'")

        if self.start_date:
            filters.append(f"date(picking.date + interval '7 hours') >= '{str(self.start_date)}'")
        if self.end_date:
            filters.append(f"date(picking.date + interval '7 hours') <= '{str(self.end_date)}'")
        if self.company_ids:
            company_ids = str(tuple(self.company_ids.ids)).replace(',)', ')')
            filters.append(f"(picking.company_id IN {company_ids} OR picking.company_id IN {company_ids})")
        else:
            branch = self.env.user._get_company_ids()
            filters.append(f"picking.company_id in {str(tuple(branch)).replace(',)', ')')}")
        if self.product_ids:
            product_ids = str(tuple(self.product_ids.ids)).replace(',)', ')')
            filters.append(f"prod.id IN {product_ids}")
        if self.partner_ids:
            partner_ids = str(tuple(self.partner_ids.ids)).replace(',)', ')')
            filters.append(f"picking.partner_id IN {partner_ids}")
        if self.categ_ids:
            categ_ids = str(tuple(self.categ_ids.ids)).replace(',)', ')')
            filters.append(f"prod_categ.id IN {categ_ids}")
        elif not self.categ_ids:
            filters.append(f"prod.division = '{self.division}'")
            
        return " AND ".join(filters)

    def action_export_report(self, return_fp=False):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        query_where = self._get_query_filters()
        query_order = "ORDER BY company.code"
        
        try:
            if self.options == 'detail_movement':
                if self.picking_type == 'internal':
                    query = self.get_query_detail_movement_internal()
                else:
                    query = self.get_query_detail_movement()

                query_in = f"{query} AND {query_where}"
                if self.picking_type == 'all' and self.division == 'Umum':
                    query_out = f"{self.get_query_detail_stock_out_movement()} AND {query_where}"
                    query = f"""
                        {query_in}
                        UNION
                        {query_out}
                    """
                else:
                    query = f"{query_in} {query_order}"
                self._cr.execute(query)
                
            elif self.options == 'outstanding':
                query = f"{self.get_query_outstanding_movement()} AND {query_where} {query_order}"
                self._cr.execute(query)
            
            result = self._cr.dictfetchall()
            return self.env['web.report'].sudo().generate_report('Report Stock Movement', result, return_fp=return_fp)
            
        except Exception as e:
            raise Warning(f"Error generating stock movement report: {str(e)}")
    