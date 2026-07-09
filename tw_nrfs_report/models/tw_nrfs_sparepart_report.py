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

class TWNRFSSparepartReport(models.TransientModel):
    _name = "tw.nrfs.sparepart.report"
    _description = "Laporan NRFS Sparepart"

    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    name = fields.Char('Nama File', readonly=True)
    start_date = fields.Date('Start date', default=_get_default_date)
    end_date = fields.Date('End date', default=_get_default_date)
    
    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query = f"""
            SELECT
                CAST(ROW_NUMBER() OVER () AS VARCHAR) AS no,
                nrfs.name AS no_nrfs,
                branch.name AS dealer,
                DATE(nrfs.nrfs_date + INTERVAL '7 hours') AS nrfs_date,
                nrfs.claim_to AS klaim_ke,
                nrfs.claim_type AS tipe_klaim,
                pt.name AS kode_part,
                pt.description AS nama_part,
                nrfsl.qty,
                lot.name AS serial_number,
                expedition.name AS expedisi,
                driver.name AS driver,
                vehicle.plate_number AS no_plate,
                pick.name AS no_internal_transfer,
                sale.name AS no_sale_order
            FROM tw_nrfs nrfs
            JOIN tw_nrfs_line nrfsl ON nrfs.id = nrfsl.nrfs_id
            LEFT JOIN res_company branch ON branch.id = nrfs.company_id
            LEFT JOIN product_product pp ON nrfsl.product_sparepart_id = pp.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN stock_lot lot ON nrfsl.lot_id = lot.id
            LEFT JOIN tw_stock_inbound inbound ON inbound.id = nrfs.stock_inbound_id
            LEFT JOIN res_partner expedition ON expedition.id = inbound.expedition_id
            LEFT JOIN res_partner driver ON driver.id = inbound.driver_id
            LEFT JOIN tw_vehicle vehicle ON vehicle.id = inbound.vehicle_id
            LEFT JOIN stock_picking pick ON pick.id = nrfs.picking_id
            LEFT JOIN tw_sale_order sale ON sale.id = nrfs.sale_order_id
            WHERE 1=1
            AND nrfs.division = 'Sparepart'
            AND nrfs.nrfs_date >= '{self.start_date}'
            AND nrfs.nrfs_date <= '{self.end_date}'
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        file_name = f"report_nrfs_sparepart_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        if ress:
            self.suspend_security().write({'name': file_name})
        return self.env['web.report'].sudo().generate_report(file_name, ress)
    