from odoo import models, fields, api, _
from datetime import datetime, timedelta

class tw_b2b_file_receive_report(models.TransientModel):
    _name = "tw.b2b.file.ssu.receive.report.wizard"
    _description = "Laporan Receive"

    @api.model
    def _get_default_date(self): 
        return fields.Date.context_today(self)

    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)

    def generate_report(self):        
        start_date = self.start_date
        end_date = self.end_date

        query = """
            SELECT 
                lot.name,
                lot.chassis_number AS chassis_no,
                lot.ship_list_number AS no_ship_list,
                pt.name->>'en_US' AS name_template,
                pt.description->>'en_US' AS description,
                pav.code,
                pav.name->>'en_US' as color_name,
                to_char(lot.receive_date + INTERVAL '7 hours', 'YYYY-MM-DD') AS tgl_receive,
                to_char(lot.ship_list_date + INTERVAL '7 hours', 'YYYY-MM-DD') AS tgl_receive_sl,
                lot.filename_ssu_md_receive AS nama_file_ssu,
                lot.actual_ssu_md_receive_date AS actual_send_ssu_receive_date, 
                wp.code 
            FROM stock_lot lot 
            JOIN res_company AS wb ON wb.id = lot.company_id 
            LEFT JOIN res_partner wp ON wp.id = wb.default_supplier_id
            JOIN product_product AS pp ON pp.id = lot.product_id 
            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id 
            LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = pp.id
            LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            WHERE 1=1
            AND lot.filename_ssu_md_receive IS NOT NULL 
            AND (lot.actual_ssu_md_receive_date + INTERVAL '7 hours')::date BETWEEN %s AND %s 
            AND wp.code IN ('MML','AHM')
        """
        
        self._cr.execute(query, (start_date, end_date))
        ress = self._cr.dictfetchall()

        return self.env['web.report'].sudo().generate_report('Laporan Receive', ress)