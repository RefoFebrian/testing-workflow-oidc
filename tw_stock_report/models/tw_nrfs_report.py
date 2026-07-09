from odoo import api, fields, models
from datetime import datetime,timedelta
from odoo.exceptions import UserError as Warning

class NrfsReport(models.TransientModel):
    _name = "tw.nrfs.report"
    _description = "NRFS Report"

    def _get_default_date(self):
        return datetime.now()

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    state = fields.Selection([
        ('identified', 'Identified by Warehouse Team'),
        ('approved', 'Approved for Vendor'),
        ('confirmed', 'Confirmed by Vendor'),
        ('in_progress', 'Repair in Progress by Vendor'),
        ('done', 'Handling Completed')
    ], string='Status')

    def action_export_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        query_where = " WHERE 1=1 "
        if self.start_date:
            query_where += f" AND nrfs.nrfs_date >= '{self.start_date}'"

        if self.end_date:
            query_where += f" AND nrfs.nrfs_date <= '{self.end_date}'"

        if self.state:
            if self.state == 'rfa':
                query_where += " AND nrfs.state IN ('draft','rfa')"
            else:
                query_where += f" AND nrfs.state = '{str(self.state)}' "

        query = f"""
            SELECT nrfs.name AS "No. NRFS"
                , nrfs.nrfs_date AS "NRFS Date"
                , nrfs.origin AS "Origin"
                , sl.name AS "No. Engine"
                , sl.chassis_number AS "No. Chassis"
                , pt.default_code AS "Product Code"
                , pt.name ->> 'en_US' AS "Product Desc"
                , (
                    SELECT to_char(DATE(tanggal + INTERVAL '7 hours'), 'YYYY-MM-DD') 
                    FROM tw_approval_line 
                    WHERE transaction_id = nrfs.id 
                    AND state = 'approve' 
                    ORDER BY id DESC LIMIT 1
                ) AS "SPK Date"
                , COALESCE(rp.name,'') AS "Vendor"
                , nrfs.urgent_po_number AS "PO Urgent"
                , nrfs.urgent_po_date AS "PO Urgent Date"
                , COALESCE(two.name,'') AS "Work Order"
                , to_char(DATE(two.confirm_date + INTERVAL '7 hours'), 'YYYY-MM-DD') AS "Start Date WO"
                , to_char(DATE(two.open_date + INTERVAL '7 hours'), 'YYYY-MM-DD') AS "Done Date WO"
            FROM tw_nrfs nrfs 
            JOIN stock_lot sl ON nrfs.lot_id = sl.id
            LEFT JOIN res_partner rp ON nrfs.branch_partner_id = rp.id 
            JOIN product_product pp ON sl.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id 
            LEFT JOIN tw_work_order two ON nrfs.id = two.nrfs_id
            {query_where}
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Report NRFS', result)
    