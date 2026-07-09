# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import re
import xlsxwriter
import calendar
from io import StringIO, BytesIO
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TWNrfsReportLkuat(models.TransientModel):
    _name = "tw.nrfs.lkuat.report"
    _description = "Report LKUAT NRFS"
    
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    name = fields.Char('Filename', readonly=True)
    start_date = fields.Date(string='Start Date', default=_get_default_date)
    end_date = fields.Date(string='End Date', default=_get_default_date)
    
    partner_ids = fields.Many2many('res.partner', string="Expedition", domain=[('category_id.name', '=', 'Expedition')])
    
    wbf = {}

    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook = self.add_workbook_format(workbook, '#FFFF00')
        date_now = datetime.now()
        get_month = date_now.strftime("%B")
        get_year = date_now.strftime("%Y")
        filename = 'Laporan_NRFS_LKUAT_' + str(get_month) + '_' + str(get_year) + '.xlsx'
        wbf = self.wbf
        rekap_data = []
        
        for partner in self.partner_ids:
            rekap_data_set = {'expedition': partner.name}
            worksheet = workbook.add_worksheet(f"{partner.name}")
            
            worksheet.set_column('A1:A1', 8)
            worksheet.set_column('B1:B1', 20)
            worksheet.set_column('C1:C1', 20)
            worksheet.set_column('D1:D1', 25)
            worksheet.set_column('E1:E1', 15)
            worksheet.set_column('F1:F1', 20)
            worksheet.set_column('G1:G1', 20)
            worksheet.set_column('H1:H1', 20)
            worksheet.set_column('I1:I1', 15)
            worksheet.set_column('J1:J1', 15)
            worksheet.set_column('K1:K1', 20)
            worksheet.set_column('L1:L1', 20)
            worksheet.set_column('M1:M1', 25)

            row = 0

            worksheet.merge_range(row, 0, row, 13, f'Rekap Potong Ongkos Angkut Unit Expedisi {partner.name}', wbf['bold_center'])
            row += 1
            worksheet.merge_range(row, 0, row, 13, f'Bulan {get_month} {get_year}', wbf['bold_center'])
            row += 2

            headers = [
                'No', 'No Polisi', 'Driver', 'Tgl Kedatangan Di Gudang', 'UNIT', 'Gejala',
                'Kode Part', 'Rincian Claim', 'Harga', 'Harga Jasa', 'No Mesin',
                'No Rangka', 'No. P.O. Pengambilan Unit'
            ]
            for col, header in enumerate(headers):
                worksheet.write(row, col, header, wbf['header'])
            row += 2 
                
            query = f"""
                SELECT 
                    vehicle.plate_number AS no_polisi,
                    driver.name AS driver,
                    pick.validate_date AS tanggal_kedatangan,
                    1 AS unit,
                    gejala.name AS gejala,
                    part.default_code AS kode_part,
                    part_tmpl.description AS rincian_claim,
                    COALESCE((part.standard_price ->> {self.env.company.id}::text)::numeric,0) AS harga,
                    COALESCE(jasa_total.harga_jasa, 0) AS harga_jasa,
                    lot.name AS no_mesin,
                    lot.chassis_number AS no_rangka,
                    lot.ship_list_number AS no_pengambilan_unit,
                    categ.name AS category
                FROM tw_nrfs nrfs
                LEFT JOIN tw_nrfs_line nrfs_line ON nrfs_line.nrfs_id = nrfs.id
                LEFT JOIN tw_nrfs_gejala_selection_rel gejala_rel ON gejala_rel.nrfs_line_id = nrfs_line.id
                LEFT JOIN tw_selection gejala ON gejala.id = gejala_rel.gejala_id
                LEFT JOIN stock_picking pick ON pick.name = nrfs.origin
                LEFT JOIN tw_stock_inbound inbound ON inbound.id = pick.stock_inbound_id
                LEFT JOIN tw_vehicle vehicle ON vehicle.id = inbound.vehicle_id
                LEFT JOIN res_partner driver ON driver.id = pick.driver_id
                LEFT JOIN product_product part ON part.id = nrfs_line.product_sparepart_id
                LEFT JOIN product_template part_tmpl ON part_tmpl.id = part.product_tmpl_id
                LEFT JOIN product_category categ ON categ.id = part_tmpl.categ_id
                LEFT JOIN stock_lot lot ON lot.id = nrfs.lot_id
                LEFT JOIN res_partner expedisi ON expedisi.id = inbound.expedition_id
                LEFT JOIN (
                    SELECT 
                        jasa_rel.line_id,
                        SUM((service.standard_price ->> {self.env.company.id}::text)::numeric) AS harga_jasa
                    FROM tw_nrfs_line_jasa_rel jasa_rel
                    JOIN product_product service ON service.id = jasa_rel.service_id
                    GROUP BY jasa_rel.line_id
                ) jasa_total ON jasa_total.line_id = nrfs_line.id
                WHERE 1=1
                AND nrfs.division = 'Unit'
                AND pick.validate_date >= '{self.start_date}'
                AND pick.validate_date <= '{self.end_date}'
                AND inbound.expedition_id = {partner.id}
            """

            self._cr.execute(query)
            data = self._cr.dictfetchall()
            sparepart_data = [item for item in data if item['category'] == 'Sparepart']
            if not sparepart_data:
                raise Warning("Data Not Found")
                
            total_unit_sparepart = 0
            total_harga_sparepart = 0
            total_jasa_sparepart = 0
            for line in sparepart_data:
                worksheet.write(row, 0, line['no'], wbf['content'])
                worksheet.write(row, 1, line['no_polisi'], wbf['content'])
                worksheet.write(row, 2, line['driver'], wbf['content'])
                worksheet.write(row, 3, line['tanggal_kedatangan'], wbf['content'])
                worksheet.write(row, 4, line['unit'], wbf['content'])
                worksheet.write(row, 5, line['gejala'], wbf['content'])
                worksheet.write(row, 6, line['kode_part'], wbf['content'])
                worksheet.write(row, 7, line['rincian_claim'], wbf['content'])
                worksheet.write(row, 8, line['harga'], wbf['content_currency'])
                worksheet.write(row, 9, line['harga_jasa'], wbf['content_currency'])
                worksheet.write(row, 10, line['no_mesin'], wbf['content'])
                worksheet.write(row, 11, line['no_rangka'], wbf['content'])
                worksheet.write(row, 12, line['no_pengambilan_unit'], wbf['content'])
                row += 1

                total_unit_sparepart += line['unit']
                total_harga_sparepart += line['harga']
                total_jasa_sparepart += line['harga_jasa']

            rekap_data_set['total_unit_sparepart'] = total_unit_sparepart
            rekap_data_set['total_harga_sparepart'] = total_harga_sparepart
            rekap_data_set['total_jasa_sparepart'] = total_jasa_sparepart
            
            worksheet.write(row, 3, "TOTAL SPAREPART", wbf['bold_center'])
            worksheet.write(row, 4, total_unit_sparepart, wbf['normal_center'])
            worksheet.write(row, 8, total_harga_sparepart, wbf['content_currency'])
            worksheet.write(row, 9, total_jasa_sparepart, wbf['content_currency'])
            
            row += 3
            worksheet.merge_range('A%s:M%s' % (row, row), "Tagihan Accesories", wbf['bold_center'])
            
            for col, header in enumerate(headers):
                worksheet.write(row, col, header, wbf['header'])
                
            row += 2
            accesories_data = [item for item in data if item['category'] == 'Sparepart']
            if not accesories_data:
                worksheet.merge_range('A%s:M%s' % (row, row), "Data Not Found", wbf['content_not_found'])
            
            total_unit_accesories = 0
            total_harga_accesories = 0
            total_jasa_accesories = 0
            for line in accesories_data:
                worksheet.write(row, 0, line['no'], wbf['content'])
                worksheet.write(row, 1, line['no_polisi'], wbf['content'])
                worksheet.write(row, 2, line['driver'], wbf['content'])
                worksheet.write(row, 3, line['tanggal_kedatangan'], wbf['content'])
                worksheet.write(row, 4, line['unit'], wbf['content'])
                worksheet.write(row, 5, line['gejala'], wbf['content'])
                worksheet.write(row, 6, line['kode_part'], wbf['content'])
                worksheet.write(row, 7, line['rincian_claim'], wbf['content'])
                worksheet.write(row, 8, line['harga'], wbf['content_currency'])
                worksheet.write(row, 9, line['harga_jasa'], wbf['content_currency'])
                worksheet.write(row, 10, line['no_mesin'], wbf['content'])
                worksheet.write(row, 11, line['no_rangka'], wbf['content'])
                worksheet.write(row, 12, line['no_pengambilan_unit'], wbf['content'])
                row += 1

                total_unit_accesories += line['unit']
                total_harga_accesories += line['harga']
                total_jasa_accesories += line['harga_jasa']
            
            rekap_data_set['total_unit_accesories'] = total_unit_accesories
            rekap_data_set['total_harga_accesories'] = total_harga_accesories
            rekap_data_set['total_jasa_accesories'] = total_jasa_accesories
            
            worksheet.write(row, 3, "TOTAL ACCESSORIES", wbf['bold_center'])
            worksheet.write(row, 4, total_unit_accesories, wbf['normal_center'])
            worksheet.write(row, 8, total_harga_accesories, wbf['content_currency'])
            worksheet.write(row, 9, total_jasa_accesories, wbf['content_currency'])
            
            row += 1
            worksheet.write(row, 3, "TOTAL JASA + PART+ ACCESSORIES", wbf['bold_center'])
            worksheet.write(row, 8, total_harga_sparepart + total_harga_accesories + total_jasa_sparepart + total_harga_accesories, wbf['content_currency'])
            rekap_data_set['total'] = total_harga_sparepart + total_harga_accesories + total_jasa_sparepart + total_harga_accesories

            row += 3
            worksheet.merge_range('A%s:N%s' % (row, row), f"Note : Harga jasa pasang & Harga HET part sesuai dengan harga dari TDM Raden Intan per {get_month} {get_year}.", wbf['bold'])

            row += 3
            worksheet.merge_range('B%s:D%s' % (row, row), 'Dibuat oleh:', wbf['normal_center'])
            worksheet.merge_range('F%s:H%s' % (row, row), 'Diketahui oleh:', wbf['normal_center'])
            worksheet.merge_range('J%s:K%s' % (row, row), 'Disetujui oleh:', wbf['normal_center'])

            row += 3
            worksheet.write(row, 1, "Adm NRFS", wbf['normal_center'])
            worksheet.write(row, 2, "Adm Receiving", wbf['normal_center'])
            worksheet.write(row, 3, "Kepala Gudang", wbf['normal_center'])
            worksheet.write(row, 5, "Logistic Manager", wbf['normal_center'])
            worksheet.write(row, 6, "Admin Manager", wbf['normal_center'])
            worksheet.write(row, 7, "GM Admin", wbf['normal_center'])
            worksheet.write(row, 9, "GM After Sales", wbf['normal_center'])
            worksheet.write(row, 10, "GM Marketing", wbf['normal_center'])
            
            rekap_data.append(rekap_data_set)
        
        # Rekapitulasi Sheet 
        worksheet = workbook.add_worksheet("Rekap")
        row1 = 0
        total_row = len(self.partner_ids) + 3
        
        worksheet.merge_range(row1, 0, row1, total_row, f'Rekap potong biaya angkut ekspedisi Unit {get_month} {get_year}', wbf['bold_center'])
        row1 += 2
        partner_names = [partner.name for partner in self.partner_ids]
        rekap_headers = ['No', 'Item Pemotongan'] + partner_names + ['Jumlah']
        for col, header in enumerate(rekap_headers):
            worksheet.write(row1, col, header, wbf['header'])
            
        row1 += 1
        items = [
            ('Unit', lambda d: d['total_unit_sparepart'] + d['total_unit_accesories'], False),
            ('Part', lambda d: d['total_harga_sparepart'], True),
            ('Jasa', lambda d: d['total_jasa_sparepart'] + d['total_jasa_accesories'], True),
            ('Accessoris', lambda d: d['total_harga_accesories'], True),
        ]
        
        no = 1
        for item_name, getter, is_currency in items:
            worksheet.write(row1, 0, no, wbf['content'])
            worksheet.write(row1, 1, item_name, wbf['content'])
            total = 0
            for idx, data in enumerate(rekap_data):
                value = getter(data)
                total += value
                if is_currency:
                    worksheet.write_number(row1, 2 + idx, value, wbf['content_currency'])
                else:
                    worksheet.write_number(row1, 2 + idx, value, wbf['content'])
            if is_currency:
                worksheet.write_number(row1, 2 + len(rekap_data), total, wbf['content_currency'])
            else:
                worksheet.write_number(row1, 2 + len(rekap_data), total, wbf['content'])
            row1 += 1
            no += 1

        # Total row
        worksheet.merge_range(row1, 0, row1, 1, 'Total', wbf['header'])

        total_sum = 0
        for idx, data in enumerate(rekap_data):
            total_val = data['total']
            total_sum += total_val
            worksheet.write_number(row1, 2 + idx, total_val, wbf['content_currency'])

        worksheet.write_number(row1, 2 + len(rekap_data), total_sum, wbf['content_currency'])
        worksheet.set_column(0, len(rekap_headers) - 1, 18)
            
        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        self.suspend_security().write({'name': filename})
        report = self.env['web.report'].suspend_security().create({
            'report_file': out,
            'name': filename,
        })
        fp.close()
        
        return {
            'type': 'ir.actions.act_url',
            "target": "new",
            'url': '/web/content/web.report/%s/report_file/%s?download=true' % (report.id, filename)
        }
        
    def add_workbook_format(self, workbook, header_color):
        self.wbf['bold'] = workbook.add_format({'bold': True})
        self.wbf['italic'] = workbook.add_format({'italic': True})
        self.wbf['bold_center'] = workbook.add_format({'bold': True, 'align': 'center'})
        self.wbf['normal_center'] = workbook.add_format({'align': 'center'})
        self.wbf['title_doc'] = workbook.add_format({'bold': 1, 'align': 'left'})
        self.wbf['title_doc'].set_font_size(12)

        self.wbf['footer'] = workbook.add_format({'align': 'left'})

        self.wbf['content_not_found'] = workbook.add_format({'italic': True, 'align': 'center'})
        self.wbf['content_not_found'].set_left()
        self.wbf['content_not_found'].set_right()
        self.wbf['content_not_found'].set_top()
        self.wbf['content_not_found'].set_bottom()
        self.wbf['content_not_found'].set_font_size(10) 
                       
        self.wbf['header'] = workbook.add_format({'bg_color': header_color, 'bold': 1, 'align': 'center', 'font_color': '#000000'})
        self.wbf['header'].set_top(2)
        self.wbf['header'].set_bottom()
        self.wbf['header'].set_left()
        self.wbf['header'].set_right()
        self.wbf['header'].set_font_size(11)
        self.wbf['header'].set_align('vcenter')

        self.wbf['content'] = workbook.add_format({'align': 'left', 'font_color': '#000000'})
        self.wbf['content'].set_left()
        self.wbf['content'].set_right()
        self.wbf['content'].set_top()
        self.wbf['content'].set_bottom()
        self.wbf['content'].set_font_size(10)                

        self.wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00'})
        self.wbf['content_float'].set_right() 
        self.wbf['content_float'].set_left()
        self.wbf['content_float'].set_top()
        self.wbf['content_float'].set_bottom()
        self.wbf['content_float'].set_font_size(10)                
        
        self.wbf['content_int'] = workbook.add_format({'align': 'right', 'num_format': '#,##0'})
        self.wbf['content_int'].set_right() 
        self.wbf['content_int'].set_left()
        self.wbf['content_int'].set_top()
        self.wbf['content_int'].set_bottom()
        self.wbf['content_int'].set_font_size(10)
        
        self.wbf['content_currency'] = workbook.add_format({'num_format': 'Rp#,##0', 'align': 'right'})
        self.wbf['content_currency'].set_right() 
        self.wbf['content_currency'].set_left()
        self.wbf['content_currency'].set_top()
        self.wbf['content_currency'].set_bottom()
        self.wbf['content_currency'].set_font_size(10)

        return workbook
