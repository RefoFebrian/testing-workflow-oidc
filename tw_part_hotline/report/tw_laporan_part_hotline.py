import io
import xlsxwriter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from xlsxwriter.utility import xl_rowcol_to_cell
import base64
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

class LaporanPartHotlineWizard(models.TransientModel):
    _name = "tw.laporan.part.hotline.wizard"
    _description = "TW Laporan Part Hotline Wizard"
    
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids.ids
        return []

    def _get_default_date(self): 
        return datetime.now()
    
    def _get_default_datetime(self):
        return fields.Datetime.now()

    name = fields.Char('Filename', readonly=True)
    options = fields.Selection([
        ('Summary', 'Summary'),
        ('Detail', 'Detail')
    ], 'Options', default='Summary')
    status = fields.Selection([
        ('Outstanding', 'Outstanding'),
        ('Done', 'Done'),
        ('All', 'All')
    ], 'Status', default='All')
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    company_ids = fields.Many2many('res.company', 'tw_part_hotline_report_company_rel', 'tw_part_hotline_id', 'company_id', default=_get_default_branch)

    def action_export(self):
        start_date,end_date = self._get_date_range()
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        query_where = " WHERE 1=1"
        query_where_po = " "
        query_where_wo = " "

        if self.company_ids:
            branch = [b.id for b in self.company_ids]
            query_where += " AND ph.company_id in %s" % str(tuple(branch)).replace(',)', ')')
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND ph.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.start_date:
            query_where += " AND ph.date >= '%s'" % self.start_date
            query_where_po += " AND po.date_order >= '%s'" % self.start_date
            query_where_wo += " AND wo.date >= '%s'" % self.start_date
        
        if self.end_date:
            query_where += " AND ph.date <= '%s'" % self.end_date
            query_where_po += " AND po.date_order <= '%s'" % self.end_date
            query_where_wo += " AND wo.date <= '%s'" % self.end_date

        if self.status == 'Outstanding':
            query_where += " AND ph.state = 'approved'"
        elif self.status == 'Done':
            query_where += " AND ph.state = 'done'"         
        else:
            query_where += " AND ph.state != 'draft'"

        if self.options == 'Summary':
            query_summary = """
                SELECT b.code as branch_code
                , b.name as branch_name
                , ph.name as hotline_name
                , ph.date as hotline_date
                , lot.name as no_engine
                , lot.chassis_number as no_chassis
                , lot.plate_number
                , p.name as customer
                , ph.customer_name
                , ph.mobile
                , sum(phd.qty) as qty_hotline
                , COALESCE(sum(quant.qty_stock),0) as qty_available
                , sum(phd.qty_po) as qty_po
                , sum(phd.qty_wo) as qty_wo
                , COALESCE(ph.amount_total,0) as total_inv
                , COALESCE(dp.amount,0) as total_hl
                , INITCAP (ph.state) as state
                , ph.po_claim_type
                , ph.po_order_date
                FROM tw_part_hotline ph
                INNER JOIN (
                    SELECT hotline_id
                    , product_id
                    , sum(qty) as qty
                    , COALESCE(sum(qty_po),0) as qty_po
                    , COALESCE(sum(qty_reserved),0) as qty_wo
                    FROM tw_part_hotline_detail GROUP BY hotline_id, product_id) as phd ON phd.hotline_id = ph.id 
                LEFT JOIN (
                    SELECT hotline_id
                    , COALESCE(sum(amount_hl_allocation),0) as amount
                    FROM tw_part_hotline_alocation_dp GROUP BY hotline_id) as dp ON dp.hotline_id = ph.id
                INNER JOIN res_company b ON b.id = ph.company_id
                LEFT JOIN (
                    SELECT l.company_id AS company_id
                    , l.warehouse_id
                    , l.complete_name AS location_name
                    , l.usage AS location_usage
                    , p.default_code
                    , p.id pid
                    , t.name AS product_name
                    , COALESCE(c.name, c2.name) AS categ_name
                    , q.product_id
                    , MIN(q.in_date) AS in_date
                    , SUM(CASE WHEN q.consolidated_date IS NOT NULL THEN q.quantity ELSE 0 END) AS qty_stock
                    , q.location_id
                    FROM stock_quant q
                    INNER JOIN stock_location l ON q.location_id = l.id AND l.usage IN ('internal','transit','nrfs')
                    LEFT JOIN product_product p ON q.product_id = p.id
                    LEFT JOIN product_template t ON p.product_tmpl_id = t.id
                    LEFT JOIN product_category c ON t.categ_id = c.id 
                    LEFT JOIN product_category c2 ON c.parent_id = c2.id 
                    WHERE 1=1 AND (c.name = 'Sparepart' OR c2.name = 'Sparepart')
                    GROUP BY l.company_id, l.warehouse_id, l.complete_name, l.usage, p.default_code, p.id, t.name, categ_name, q.product_id, q.location_id
                ) AS quant on quant.pid = phd.product_id AND quant.company_id = ph.company_id
                INNER JOIN stock_lot lot ON lot.id = ph.lot_id
                INNER JOIN res_partner p ON p.id = ph.customer_id
                %s
                GROUP BY b.code, b.name, ph.id, lot.name, lot.chassis_number, lot.plate_number, p.name, dp.amount
            """ %(query_where)
            query = query_summary 
        else:
            query_detail = """
                SELECT b.code as branch_code
                , b.name as branch_name
                , ph.po_claim_type
                , ph.name as hotline_name
                , ph.date as hotline_date
                , lot.name as no_engine
                , lot.chassis_number as no_chassis
                , lot.plate_number
                , p.name as customer
                , ph.customer_name
                , ph.mobile
                , pt.name->>'en_US' as product
                , pp.default_code as description
                , phd.qty as qty_hotline
                , phd.price
                , COALESCE(po.product_qty,COALESCE(phd.qty_po,0)) as qty_po
                , COALESCE(ail.consolidated_qty,0) as qty_consolidate
                , CASE WHEN (po.product_qty > 0 or phd.qty_po > 0) THEN COALESCE(po.name,phd.no_po) ELSE NULL END  as po_name
                , CASE WHEN (po.product_qty > 0 or phd.qty_po > 0) THEN COALESCE(to_char(po.date_order + interval '7 hours','YYYY-MM-DD'),to_char(phd.po_date,'YYYY-MM-DD')) ELSE NULL END as po_date
                , CASE WHEN (wo.product_qty > 0 and phd.qty_reserved > 0) THEN COALESCE(wo.product_qty,COALESCE(phd.qty_reserved,0)) ELSE 0 END as qty_wo
                , CASE WHEN (wo.product_qty > 0 and phd.qty_reserved > 0) THEN wo.date ELSE NULL END as wo_date
                , CASE WHEN (wo.product_qty > 0 and phd.qty_reserved > 0) THEN COALESCE(wo.name,phd.no_wo) ELSE NULL END  as wo_name
                , date_part('days',wo.date - COALESCE(po.date_order,phd.po_date)) as umur
                , INITCAP (ph.state) as state
                , ph.po_order_date
                FROM tw_part_hotline ph
                INNER JOIN tw_part_hotline_detail phd ON phd.hotline_id = ph.id 
                INNER JOIN res_company b ON b.id = ph.company_id
                INNER JOIN stock_lot lot ON lot.id = ph.lot_id
                INNER JOIN res_partner p ON p.id = ph.customer_id
                INNER JOIN product_product pp ON pp.id = phd.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN (
                    SELECT po.id
                    , po.name
                    , date_order
                    , po.part_hotline_id
                    , pol.product_id
                    , COALESCE(pol.product_qty,0) as product_qty
                    FROM purchase_order po
                    INNER JOIN purchase_order_line pol ON pol.order_id = po.id
                    WHERE po.state in ('approved','done')
                    AND po.part_hotline_id IS NOT NULL
                    %s
                ) po ON po.part_hotline_id = ph.id and po.product_id = phd.product_id
                LEFT JOIN (
                    SELECT wo.id
                    , wo.name
                    , wo.date
                    , wol.part_hotline_id
                    , wol.product_id
                    , COALESCE(wol.product_uom_qty,0) as product_qty
                    FROM tw_work_order wo
                    INNER JOIN tw_work_order_line wol ON wol.order_id = wo.id
                    WHERE wo.state in ('sale','done')
                    AND wol.part_hotline_id IS NOT NULL
                    %s
                ) wo ON wo.part_hotline_id = ph.id and wo.product_id = phd.product_id
                LEFT JOIN account_move ai ON ai.invoice_origin = po.name AND ai.state in ('posted','paid')
                LEFT JOIN account_move_line ail ON ail.move_id = ai.id AND ail.product_id = po.product_id
                %s
                ORDER BY ph.name ASC
            """ %(query_where_po,query_where_wo,query_where)
            query = query_detail

        self._cr.execute (query)
        ress =  self._cr.dictfetchall()
        if not ress:
            raise Warning("Data tidak ditemukan")
        return self.env['web.report'].sudo().generate_report('Laporan Part Hotline',ress, data_summary_header=False, start_date=start_date, end_date=end_date,freeze_panes_column=3)

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