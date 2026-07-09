# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
import calendar

class TWLaporanRincianKendaraan(models.TransientModel):
    _name = "tw.laporan.rincian.kendaraan"
    _description = "TW Laporan Rincian Kendaraan"

    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return [company_ids[0].id]
        return []
        
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
    
    name = fields.Char(string="Filename", readonly=True)
    file = fields.Binary(string="File", readonly=True)
    company_ids = fields.Many2many('res.company', string="Branch", default=_get_default_branch)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    tgl_beli = fields.Date(string="Tanggal Beli", default=_get_default_date)

    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = "WHERE dso.state in ('approved','sale')"

        if self.company_ids:
            query_where += f" AND dso.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            companies = self.env.user._get_company_ids()
            query_where += f" AND dso.company_id IN {str(tuple(companies)).replace(',)', ')')}"

        if self.start_date:
            query_where += " AND dso.date_order >= '%s'" % str(self.start_date)
        if self.end_date:
            query_where += " AND dso.date_order <= '%s'" % str(self.end_date)
        
        summary_header = self._get_summary_header_data()
        query = """
            SELECT
                b.name as nama_dealer
                , b.street || ' ' || COALESCE(kec.name,' ') || ' ' || COALESCE(city.name,' ') as alamat_dealer
                , COALESCE(b.vat,'-') as npwp_perusahaan
                , COALESCE(tbs.taxable_person,'-') as no_pengukuhan_pkp
                , COALESCE(fpo.name,'-') as faktur_pajak
                , fpo.date as tanggal_faktur
                , p.name as nama_pembeli
                , COALESCE(p.identification_number,'-') as no_KTP_pembeli
                , p.street || ', RT '|| COALESCE(p.rt,' ') || '/' || COALESCE(p.rw,' ') || ' ' || COALESCE(kec2.name,'') || ' - ' || COALESCE(kel.name,'') || ' ' || COALESCE(city.name,' ') as alamat_pembeli
                , lot.name as no_mesin
                , lot.chassis_number as no_rangka
                , COALESCE(pt.name ->>'id_ID', pt.name ->>'en_US', '') || ' (' || COALESCE(pav.name->>'id_ID', pav.name->>'en_US', '') || ')' as tipe
                , COALESCE(pp.default_code,'-') as jenis
                , COALESCE(lot.production_year ,'-') as tahun
                , ROUND(dsol.price_unit / (COALESCE(at.amount + 100)/100),2) as harga_jual_kendaraan
                , ROUND(dsol.price_unit  - (dsol.price_unit / (COALESCE(at.amount + 100)/100)),2) as ppn
                , '-' as ppn_bn
                , dsol.price_unit as jumlah
                , '-' as keterangan
            FROM tw_dealer_sale_order dso
            INNER JOIN tw_dealer_sale_order_line dsol ON dsol.order_id = dso.id
            LEFT JOIN tw_dealer_sale_order_line_tax_rel dsot ON dsot.order_line_id = dsol.id
            LEFT JOIN account_tax at ON at.id = dsot.tax_id
            LEFT JOIN tw_faktur_pajak_out fpo ON fpo.id = dso.faktur_pajak_out_id
            INNER JOIN stock_lot lot ON lot.id = dsol.lot_id
            INNER JOIN product_product pp ON pp.id = lot.product_id
            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN (SELECT DISTINCT ON (product_tmpl_id) * FROM product_template_attribute_value ORDER BY product_tmpl_id, id) AS f ON f.product_tmpl_id = pt.id
            LEFT JOIN product_attribute_value pav ON pav.id = f.product_attribute_value_id                      
            INNER JOIN res_company c ON c.id = dso.company_id 
            inner join res_partner b on b.id = c.partner_id
            left join tw_branch_setting tbs on tbs.company_id = c.id 
            LEFT JOIN res_city city ON city.id = b.city_id
            LEFT JOIN res_district kec ON kec.id = b.district_id
            INNER JOIN res_partner p ON p.id = dso.partner_id
            LEFT JOIN res_city city2 ON city2.id = p.city_id
            LEFT JOIN res_district kec2 ON kec2.id = p.district_id 
            LEFT JOIN res_sub_district kel ON kel.id = p.sub_district_id 
            %s
            """ % (query_where)
            
        self.env.cr.execute(query)
        rows = self.env.cr.dictfetchall()
        if not rows:
            raise Warning('Data tidak ada...')
        report_name = f"Laporan Rincian Kendaraan"
        return self.env['web.report'].sudo().generate_report(report_name, rows,show_total_footer=False,data_summary_header=summary_header,data_summary_header_col_size=False)
            
    def _get_summary_header_data(self):
        date= self._get_default_date()
        month = False
        tahun = False
        if self.tgl_beli:
            month = calendar.month_name[self.tgl_beli.month]
            tahun = self.tgl_beli.year
        return {
            "A2": "LAMPIRAN SURAT KEDARAN NOMOR : SE-31/PJ/2013 TANGGAL 5 JULI 2013 TENTANG PELAPORAN PEMUNGUTAN PPN DAN PPnBM ATAS PENYERAHAN KENDARAAN BERMOTOR",
            "A4": "DAFTAR RINCIAN KENDARAAN BERMOTOR",
            "A5": "BULAN %s TAHUN %s" % (month, tahun),
        }
        