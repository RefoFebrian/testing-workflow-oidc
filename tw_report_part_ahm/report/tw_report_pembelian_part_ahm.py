# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import datetime, timedelta

class TWReportPembelianPartAhm(models.TransientModel):
    _name = "tw.report.pembelian.part.ahm"
    _description = "TW Report Pembelian Part AHM"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    name = fields.Char('Filename',readonly=True)
    company_ids = fields.Many2many('res.company',string="Branch")
    start_date = fields.Date('Start Date',default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    division  = fields.Selection([('Unit','Unit'),('Sparepart','Sparepart')],default="Sparepart")
    file = fields.Binary(string="File")

    def generate_report(self,return_fp=False):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        
        query_where = "WHERE 1=1 AND spa.state = 'done' AND spi.partner_id = b.default_supplier_id AND ts.value = 'MD'"

        if self.division:
            query_where += " AND spi.division = '%s'" % self.division
        if self.start_date:
            query_where += " AND (spi.date + INTERVAL '7 hours')::date >= '%s'" % self.start_date
        if self.end_date:
            query_where += " AND (spi.date + INTERVAL '7 hours')::date <= '%s'" % self.end_date

        query = """
        SELECT 
            b.code as branch_code,
            b.name as branch_name,
            p.name as supplier,
            spb.name as packing_name,
            spi.name as picking_name,
            pp.default_code as part_code,
            COALESCE(pt.name->>'en_US',pt.name->>'id_ID')  as part_name,
            SUM(spal.quantity) as quantity,
            string_agg(DISTINCT inv.name, ',') as invoice,
            string_agg(DISTINCT fdo.no_invoice, ',') as invoice_ahm,
            string_agg(DISTINCT ps.po, ',') as po,
            spi.origin as kode_ps,
            string_agg(DISTINCT sqp.name,',') as no_kardus
            FROM stock_picking spi
            left JOIN stock_picking_stock_picking_batch_rel rel
			    ON rel.stock_picking_id = spi.id
			left JOIN stock_picking_batch spb
			    ON spb.id = rel.stock_picking_batch_id
            INNER JOIN stock_move spa ON spa.picking_id = spi.id
            INNER JOIN res_company b on b.id = spi.company_id
            INNER JOIN tw_selection ts ON ts.id = b.branch_type_id
            LEFT JOIN res_partner p ON p.id = b.default_supplier_id
            INNER JOIN stock_move_line spal ON spal.move_id = spa.id
            left join stock_quant_package sqp on sqp.id = spal.result_package_id
            INNER JOIN product_product pp ON pp.id = spal.product_id
            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
	           left JOIN (
			         select
			             tbbf.name,
			             ps.value AS kode_ps,
			             dus.value AS kode_dus,
			             code.value AS kode_sparepart,
                         po.value as po
			         FROM tw_b2b_file_content tbbfc
			         JOIN tw_b2b_file tbbf ON tbbf.id = tbbfc.file_id
			         JOIN tw_b2b_file_content_line ps ON ps.file_content_id = tbbfc.id and ps.name ='kode_ps'
			         JOIN tw_b2b_file_content_line dus ON dus.file_content_id = tbbfc.id and dus.name ='kode_dus'
			         JOIN tw_b2b_file_content_line code ON code.file_content_id = tbbfc.id and code.name ='kode_sparepart'
                     JOIN tw_b2b_file_content_line po ON po.file_content_id = tbbfc.id and po.name ='kode_po_md'
			         WHERE tbbf.ext = 'PS'
			         GROUP BY tbbf.id, ps.value, dus.value, code.value, po.value
			     ) ps ON ps.kode_ps = spi.origin and ps.kode_dus = sqp.name
			join (SELECT
				        tbbfc.id AS file_content_id,
				        MAX(CASE WHEN tbbfcl.name = 'kode_ps' THEN tbbfcl.value END)  AS kode_ps,
				        MAX(CASE WHEN tbbfcl.name = 'no_invoice' THEN tbbfcl.value END) AS no_invoice,
				        MAX(CASE WHEN tbbfcl.name = 'kode_sparepart' THEN tbbfcl.value END) AS kode_sparepart
				    FROM tw_b2b_file_content tbbfc
				    JOIN tw_b2b_file tbbf
				        ON tbbf.id = tbbfc.file_id
				    JOIN tw_b2b_file_content_line tbbfcl
				        ON tbbfcl.file_content_id = tbbfc.id
				    WHERE tbbf.ext = 'FDO'
				      AND tbbfcl.name IN ('kode_ps', 'no_invoice','kode_sparepart')
				    GROUP BY tbbfc.id) fdo on fdo.kode_sparepart = ps.kode_sparepart and fdo.kode_ps = ps.kode_ps  
            LEFT JOIN account_move inv ON inv.ref  = fdo.no_invoice 
            %s
            GROUP BY b.code,b.name,p.name,spi.name,pt.name,pp.default_code,spal.quantity,spi.origin,spb.name
        """ % query_where

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        if not ress:
            raise Warning('Data tidak ada...')
        report_name = f"Laporan Pembelian Part AHM"
        return self.env['web.report'].sudo().generate_report(report_name, ress,show_total_footer=False,return_fp=return_fp)
    