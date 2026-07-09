# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import xlsxwriter
from io import StringIO,BytesIO
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWNRFSPoUrgentReport(models.TransientModel):
    _name = "tw.nrfs.po.urgent.report"
    _description = "Laporan PO Urgent"

    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    name = fields.Char('Nama File', readonly=True)
    start_date = fields.Date('Start date', default=_get_default_date)
    end_date = fields.Date('End date', default=_get_default_date)
    
    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query = f"""
            SELECT
                pt.default_code AS kode_part,
                pt.name ->> 'en_US' as description_part,
                nrfsl.qty,
                nrfs.urgent_po_number,
                nrfs.urgent_po_date,
                DATE(nrfs.urgent_po_date + INTERVAL '10 days') AS tanggal_pengiriman,
                nrfs.name AS source_document,
                lot.name AS no_mesin,
                lot.chassis_number AS no_rangka,
                pt_unit.default_code AS tipe_unit,
                pt_unit.name ->> 'en_US' AS description_unit,
                lot.production_year AS tahun_produksi,
                p.name AS nama_konsumen,
                COALESCE(p.street,'') AS alamat_konsumen,
                COALESCE(city.name,'') AS kota_konsumen,
                COALESCE(p.mobile,p.phone) AS no_telp,
                COALESCE(nrfs.urgent_ppo_filename) AS nama_file_ppo,
                COALESCE(nrfs.urgent_ppo_send_date) AS tgl_kirim_ppo,
                COALESCE(nrfsl.distribution_number) AS distribution_number
            FROM tw_nrfs nrfs
            JOIN tw_nrfs_line nrfsl ON nrfs.id = nrfsl.nrfs_id
            JOIN product_product pp ON nrfsl.product_sparepart_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN stock_lot lot ON nrfs.lot_id = lot.id
            JOIN product_product pp_unit ON lot.product_id = pp_unit.id
            JOIN product_template pt_unit ON pp_unit.product_tmpl_id = pt_unit.id
            JOIN res_partner p ON nrfs.branch_partner_id = p.id
            LEFT JOIN res_city city on p.city_id = city.id
            WHERE 1=1
            AND nrfs.division = 'Unit'
            AND nrfsl.is_order_sparepart = True
            AND nrfs.nrfs_date >= '{self.start_date}'
            AND nrfs.nrfs_date <= '{self.end_date}'
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if ress:
            self.suspend_security().write({'name': 'Report PO Urgent'})
        return self.env['web.report'].sudo().generate_report('Report PO Urgent', ress)
