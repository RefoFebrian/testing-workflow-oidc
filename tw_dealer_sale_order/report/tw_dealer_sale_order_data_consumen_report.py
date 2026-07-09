# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwDealerSaleOrderDataConsumenReport(models.TransientModel):
    _name = "tw.dealer.sale.order.data.consumen.report"
    _description = "Dealer Sale Order Data Consumen Report"


    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    company_ids = fields.Many2many('res.company','tw_dso_data_consumen_company_rel', 'report_id', 'company_id', string="Branch")

    def onchange_date(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise UserError('Start Date must be less than End Date')

    def action_export_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        
        query_where = ""
        if self.start_date:
            query_where += f" AND dso.date_order >= '{self.start_date}'" 

        if self.end_date:
            query_where += f" AND dso.date_order <= '{self.end_date}'"
        
        if self.company_ids:
            query_where += f" AND dso.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND dso.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        query = f"""
            SELECT 
                b.code as branch_code
                , b.name as branch_name 
                , COALESCE(cdb.mobile,'') as no_hp
                , COALESCE(cdb.name,'') as nama
                , COALESCE(ts_gender.name,'') as jenis_kelamin
                , cdb.birthdate as tgl_lahir
                , dso.date_order as tgl_beli
                , COALESCE(ts_agama.name,'') as agama
                , COALESCE(product.default_code ,'') as tipe 
                , COALESCE(pav.name ->>'en_US','') as color
                , lot.registration_handover_date as tgl_penyerahan_stnk
                , lot.plate_handover_date as tgl_penyerahan_bpkb
                , COALESCE(ts_pekerjaan.name,'') as pekerjaan
                , COALESCE(cdb.street || ' ','') || COALESCE(cdb.street2,'') as alamat
                , COALESCE(cdb.rt,'') as rt
                , COALESCE(cdb.rw,'') as rw
                , COALESCE(sub_dist.name,'') as kelurahan
                , COALESCE(dist.name,'') as kecamatan
                , COALESCE(city.name,'') as kota
                , COALESCE(state.name,'') as propinsi
                , dso.name as no_faktur
                , lot.name as no_mesin
            FROM tw_dealer_sale_order dso 
            INNER JOIN tw_dealer_sale_order_line dsol on dso.id = dsol.order_id and dsol.lot_id notnull
            INNER JOIN res_company b on dso.company_id = b.id 
            INNER JOIN tw_partner_cdb cdb on dso.cdb_stnk_id = cdb.id 
            INNER JOIN res_partner rp on dso.partner_id = rp.id
            LEFT JOIN product_product product ON dsol.product_id = product.id 
            LEFT JOIN product_variant_combination as pvc on pvc.product_product_id = product.id
            LEFT JOIN product_template_attribute_value as ptav on ptav.id = pvc.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            LEFT JOIN stock_lot lot on dsol.lot_id = lot.id
            LEFT JOIN tw_selection ts_gender on cdb.gender_id = ts_gender.id
            LEFT JOIN tw_selection ts_agama on cdb.religion_id = ts_agama.id
            LEFT JOIN tw_selection ts_pekerjaan on cdb.occupation_id = ts_pekerjaan.id
            LEFT JOIN res_sub_district sub_dist on sub_dist.id = cdb.sub_district_id
            LEFT JOIN res_district dist on dist.id = cdb.district_id
            LEFT JOIN res_city city on city.id = cdb.city_id
            LEFT JOIN res_country_state state on state.id = cdb.state_id
            WHERE dso.state in ('sale', 'done')
            {query_where}
        """

        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Laporan Data Konsumen', result)
    
