from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError as Warning

class TravelDocumentReport(models.TransientModel):
    _name = "tw.travel.document.report"
    _description = "Surat Jalan Report"

    def _get_default_date(self):
        return datetime.now()
    
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    options = fields.Selection([
        ('outgoing', 'Outgoing Surat Jalan'),
        ('incoming', 'Incoming Surat Jalan'),
        ('mutation', 'Mutated Surat Jalan'),
    ], string='Document Direction', default='outgoing')

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)

    company_ids = fields.Many2many(comodel_name='res.company', relation='tw_travel_document_report_company_rel',
                                  column1='travel_document_id', column2='company_id', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)], store=True)

    def action_export_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        query_where = ""

        if self.company_ids :
            company_ids = str(tuple([b.id for b in self.company_ids])).replace(',)', ')')
            query_where += f" AND sp.company_id in {company_ids} "
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND sp.company_id in {str(tuple(branch)).replace(',)', ')')}"

        if self.start_date:
            query_where += f" AND (sp.validate_date + INTERVAL '7 hours')::date >= '{self.start_date}'"
        
        if self.end_date :
            query_where += f" AND (sp.validate_date + INTERVAL '7 hours')::date <= '{self.end_date}'"

        query_where += f" AND pp.division = '{self.division}'"

        if self.options == 'outgoing':
            spt_code = "IN ('interbranch_out','outgoing')"
        elif self.options == 'incoming':
            spt_code = "IN ('interbranch_in','incoming')"
        else :
            spt_code = "='internal'"

        query_where += f" AND spt.code {spt_code}"

        query = f"""
            SELECT DISTINCT rc.code AS "Branch Code"
                , rc.name AS "Branch Name"
                , sp.origin AS "Origin"
                , rp.code AS "Requester / Sender Code"
                , rp.name AS "Requester / Sender Name"
                , sp.name AS "No. Picking"
                , to_char(sp.validate_date + INTERVAL '7 hours', 'YYYY-MM-DD') AS "Picking Date"
                , sp.state AS "Status"
                , sp.division AS "Division"
                , spt.name->>'en_US' AS "Jenis Transaksi"
                , spb.name AS "Surat Jalan"
                , sl.name AS "No. Engine"
                , sl.chassis_number AS "No. Chassis"
                , pp.default_code AS "Product"
                , pav.code AS "Color Code"
                , pav.name->>'en_US' AS "Color"
                , driver.name AS "Driver"
            FROM stock_picking sp
            LEFT JOIN stock_picking_type spt on sp.picking_type_id = spt.id
            LEFT JOIN stock_picking_stock_picking_batch_rel rel
			    ON rel.stock_picking_id = sp.id
			LEFT JOIN stock_picking_batch spb
			    ON spb.id = rel.stock_picking_batch_id
            LEFT JOIN res_company rc on sp.company_id = rc.id
            LEFT JOIN res_partner rp on sp.partner_id = rp.id
            LEFT JOIN res_partner driver on sp.driver_id = driver.id
            LEFT JOIN stock_move sm on sp.id = sm.picking_id 
            LEFT JOIN product_product pp on sm.product_id = pp.id
            LEFT JOIN product_variant_combination as pvc on pvc.product_product_id = pp.id
            LEFT JOIN product_template_attribute_value as ptav on ptav.id = pvc.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            LEFT JOIN stock_move_line sml on sm.id = sml.move_id 
            LEFT JOIN stock_lot sl on sml.lot_id = sl.id
            LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
            LEFT JOIN product_category pc on pc.id = pt.categ_id
            WHERE 1=1
            {query_where}
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Report Surat Jalan', result)
    
