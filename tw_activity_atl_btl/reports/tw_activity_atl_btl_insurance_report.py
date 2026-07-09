# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import pytz
import base64
import csv
import xlsxwriter
import calendar
from io import StringIO,BytesIO
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TWActivityPlanInsuranceReport(models.TransientModel):
    _name = "tw.activity.atl.btl.insurance.report"
    _description = "Report Insurance Activity Plan"

    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return [(6, 0, company_ids.ids)]    
        return False
    
    def _get_default_date(self):
        return datetime.now()

    def _get_year(self):
        return date.today().year
    
    name = fields.Char('Filename', readonly=True)
    month = fields.Selection([(str(i), (calendar.month_name[i])) for i in range(1, 13)], 'Month')
    year = fields.Char('Tahun', default=_get_year)
    base_price = fields.Float('Base Price',default=15000000)
    
    data_x = fields.Binary('File', readonly=True)
    
    company_ids = fields.Many2many(
                    'res.company',
                    string='Companies',
                    default=_get_default_branch
                )

    def action_generate_report(self):
        month = self.month
        year = self.year
        company_ids = self.company_ids
        
        query_where = f" WHERE 1=1 AND act_type.is_location = True AND btl_line.state in ('confirmed','done') "
        
        if month:
            query_where += f" AND btl.month = '{month}'"

        if year:
            query_where += f" AND btl.year = '{year}'"

        if company_ids:
            query_where += f" AND btl.company_id IN {str(tuple([b.id for b in self.company_ids])).replace(',)', ')')}"

        query = f"""
            select 
                b.code as induk_lokasi
                , b.name as cabang_induk
                , COALESCE(rp.street, '-') || ' Rt.' || COALESCE(b.rt, '-') || ' Rw.' || COALESCE(b.rw, '-') || ', Kelurahan ' || INITCAP(COALESCE(rsd."name", '-')) || ', Kecamatan ' || INITCAP(COALESCE(rd."name", '-')) || ', ' || INITCAP(COALESCE(rc.name, '-')) || ', Provinsi ' || INITCAP(COALESCE(rcs.name, '-')) AS alamat_cabang_induk
                , sl.name AS nama_lokasi
                , COALESCE(btl_line.street,'-') ||' Rt.'||COALESCE(btl_line.rt,'-')||' Rw.'||COALESCE(btl_line.rw,'-')||', Kelurahan '||initcap(COALESCE(rsd_act.name,'-'))||', Kecamatan '||initcap(COALESCE(rd_act.name,'-'))||', '||initcap(COALESCE(rc_act.name,'-'))||', Provinsi '||initcap(COALESCE(rcs_act.name,'-')) as alamat
                , to_char(btl_line.start_date, 'DD Mon YYYY') as awal
                , to_char(btl_line.end_date, 'DD Mon YYYY') as akhir
                , (btl_line.display_unit * {self.base_price}) as nilai
            from tw_activity_atl_btl btl
            inner join tw_activity_atl_btl_line btl_line on btl.id = btl_line.activity_id 
            inner join res_company b on b.id = btl.company_id 
            inner join res_partner rp on rp.id = b.partner_id 
            inner join stock_location sl on sl.id = btl_line.location_id 
            inner join tw_master_activity_type act_type on act_type.id = btl_line.act_type_id 
            left join res_sub_district rsd on rsd.id = b.sub_district_id 
            left join res_district rd on rd.id = b.district_id 
            left join res_city rc on rc.id = b.city_id 
            left join res_country_state rcs on rcs.id = rc.state_id
            INNER JOIN tw_mapping_titik_keramaian mtk ON mtk.id = btl_line.mapping_activity_id
            INNER JOIN tw_titik_keramaian tk ON tk.id = mtk.activity_point_id 
            left join res_sub_district rsd_act on rsd_act.id = btl_line.sub_district_id 
            left join res_district rd_act on rd_act.id = tk.district_id 
            left join res_city rc_act on rc_act.id = rd_act.city_id 
            left join res_country_state rcs_act on rcs_act.id = rc_act.state_id
            {query_where}
        """

        self._cr.execute(query)
        ress =  self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Report Insurance Activity Plan',ress)
    
