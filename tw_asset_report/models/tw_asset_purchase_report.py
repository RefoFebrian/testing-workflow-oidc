from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AssetPurchaseReport(models.TransientModel):
    _name = "tw.asset.purchase.report"
    _description = "Asset Purchase Report"

    purchase_state = fields.Selection([
        ('all', 'All'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('acquisitioned', 'Acquisitioned')],
        'Purchase State',
        required=True,
        default='all')

    po_date_start = fields.Date('PO Date Start', default=lambda self: fields.Date.context_today(self).replace(day=1))
    po_date_end = fields.Date('PO Date End', default=lambda self: fields.Date.context_today(self))
    gr_date_start = fields.Date('GR Date Start')
    gr_date_end = fields.Date('GR Date End')
    acq_date_start = fields.Date('Acquisition Date Start')
    acq_date_end = fields.Date('Acquisition Date End')

    company_ids = fields.Many2many('res.company', 'tw_asset_purchase_report_company_rel', 'report_id', 'company_id', string="Branch")
    category_ids = fields.Many2many('account.asset.category', 'tw_asset_purchase_report_category_rel', 'report_id', 'category_id', string='Category')

    def action_export_report(self, return_fp=False):
        if not (self.po_date_start or self.po_date_end or self.gr_date_start or self.gr_date_end or self.acq_date_start or self.acq_date_end):
            raise ValidationError(_("Silakan isi minimal satu filter tanggal (Tanggal PO, Tanggal GR, atau Tanggal Akuisisi)."))

        query_where = "WHERE 1=1 "
        
        # Company filtering
        if self.company_ids:
            query_where += f" AND po.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND po.company_id IN {str(tuple(branch)).replace(',)', ')')}"
        
        # Category filtering
        if self.category_ids:
            category_ids = str(tuple([b.id for b in self.category_ids])).replace(',)', ')')
            query_where += f" AND COALESCE(asset.category_id, gr_line.asset_category_id) in {category_ids}"
        
        # Date Range Filters
        if self.po_date_start:
            query_where += f" AND po.date_order::date >= '{self.po_date_start}'"
        if self.po_date_end:
            query_where += f" AND po.date_order::date <= '{self.po_date_end}'"
        
        if self.gr_date_start:
            query_where += f" AND gr.date >= '{self.gr_date_start}'"
        if self.gr_date_end:
            query_where += f" AND gr.date <= '{self.gr_date_end}'"
        
        if self.acq_date_start:
            query_where += f" AND acq.date >= '{self.acq_date_start}'"
        if self.acq_date_end:
            query_where += f" AND acq.date <= '{self.acq_date_end}'"
        
        # State Filtering
        if self.purchase_state == 'ordered':
            query_where += " AND gr_line.id IS NULL"
        elif self.purchase_state == 'received':
            query_where += " AND gr_line.id IS NOT NULL AND acq.id IS NULL"
        elif self.purchase_state == 'acquisitioned':
            query_where += " AND acq.id IS NOT NULL AND asset.id IS NOT NULL"

        query = f"""
            SELECT 
                branch.code AS "Branch Code",
                po.name AS "PO Number",
                po.date_order::date AS "PO Date",
                partner.name AS "Vendor",
                COALESCE(pt.name->>'en_US', '') AS "Product",
                gr.name AS "GR Number",
                gr.date AS "GR Date",
                acq.name AS "Acquisition Number",
                acq.date AS "Acquisition Date",
                asset.name AS "Regas Number",
                asset.code AS "Asset Code",
                asset.value AS "Value",
                INITCAP(asset.state) AS "Asset State"
            FROM purchase_order_asset_line po_line
            JOIN purchase_order_asset po ON po.id = po_line.order_id
            LEFT JOIN res_partner partner ON partner.id = po.partner_id
            LEFT JOIN res_company branch ON branch.id = po.company_id
            LEFT JOIN product_product pp ON pp.id = po_line.product_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN tw_good_receive_asset_line gr_line ON gr_line.purchase_order_line_id = po_line.id AND gr_line.state != 'cancel'
            LEFT JOIN tw_good_receive gr ON gr.id = gr_line.picking_id AND gr.state != 'cancel'
            LEFT JOIN tw_asset_acquisition acq ON acq.good_receive_line_id = gr_line.id AND acq.state != 'cancel'
            LEFT JOIN account_asset_good_receive_line_rel rel ON rel.gr_line_id = gr_line.id
            LEFT JOIN account_asset_asset asset ON (asset.id = rel.asset_id OR asset.acquisition_id = acq.id) AND asset.state != 'cancel'
            {query_where}
            ORDER BY po.date_order DESC, po.name DESC
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Laporan Pembelian Asset', result, capitalize=False, return_fp=return_fp)
