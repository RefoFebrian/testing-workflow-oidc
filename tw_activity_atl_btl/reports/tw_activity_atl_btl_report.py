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

class TWActivityPlanReport(models.TransientModel):
    _name = "tw.activity.atl.btl.plan.report"
    _description = "Report Activity Plan"

    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return [(6, 0, company_ids.ids)]    
        return False

    def _get_year(self):
        return date.today().year
    
    name = fields.Char('Filename', readonly=True)
    month = fields.Selection([(str(i), (calendar.month_name[i])) for i in range(1, 13)], 'Month')
    year = fields.Char('Tahun', default=_get_year)
    options = fields.Selection([
        ('all','All'),
        ('open','Open'),
        ('confirm_done','Confirm & Done'),
        ('reject','Reject')],string="Options" ,default="confirm_done")
    
    data_x = fields.Binary('File', readonly=True)
    
    company_ids = fields.Many2many('res.company', 'tw_activity_atl_btl_report_wizard_company', 'tw_activity_atl_btl_report_wizard_id','company_id', "Branch", default=_get_default_branch)

    def action_generate_report(self):
        month = self.month
        year = self.year
        company_ids = self.company_ids

        query_where = f" WHERE pa.state != 'draft' AND pa.month = '{month}' AND pa.year = '{year}'"

        if company_ids:
            query_where += f" AND pa.company_id IN {str(tuple([b.id for b in self.company_ids])).replace(',)', ')')}"
        
        if self.options == 'open':
            query_where += " AND pal.state = 'open'"
        elif self.options == 'confirm_done':
            query_where += " AND pal.state in ('confirmed','done')"
        elif self.options == 'reject':
            query_where += " AND pal.state = 'reject'"

        query = f"""
            SELECT
            b.code as branch_code
            , b.name as branch_name
            , CASE WHEN pa.month = '1' THEN 'Januari'
            WHEN pa.month = '2' THEN 'Februari'
            WHEN pa.month = '3' THEN 'Maret'
            WHEN pa.month = '4' THEN 'April'
            WHEN pa.month = '5' THEN 'Mei'
            WHEN pa.month = '6' THEN 'Juni'
            WHEN pa.month = '7' THEN 'Juli'
            WHEN pa.month = '8' THEN 'Agustus'
            WHEN pa.month = '9' THEN 'September'
            WHEN pa.month = '10' THEN 'Oktober'
            WHEN pa.month = '11' THEN 'November'
            WHEN pa.month = '12' THEN 'Desember'
            END ||'-' || pa.year as periode
            , pal.name as activity
            , sc.name as jaringan_penjualan
            , pal.display_unit
            , pal.target_unit
            , pal.target_customer
            , pal.phone_number as no_telp
            , pal.street || ', RT/RW: '|| coalesce(pal.rt,'-') || '/' || coalesce(pal.rw,'-') as alamat
            , pal.state as status_detail 
            , sp.name as type_act
            , tk.name as titik_keramaian
            , tr.name as ring
            , COALESCE(pal.total_cost,0) as biaya
            , city.name as city
            , kec.name as kecamatan
            , kel.name as kelurahan
            , hr.name as pic
            , COALESCE(to_char(pal.start_date, 'DD-Mon-YYYY'),'') as start_date
            , COALESCE(to_char(pal.end_date, 'DD-Mon-YYYY'),'') as end_date
            , CASE
                WHEN sp.is_location THEN 'Ya'
                ELSE 'Tidak'
            END as "Location?"
            , loc.complete_name as location
            , (SELECT count(id) FROM tw_dealer_spk WHERE activity_plan_id = pal.id) as actual_customer
            , (
                SELECT COALESCE(sum(dsol.product_uom_qty), 0)
                FROM tw_dealer_sale_order dso 
                INNER JOIN tw_sale_order_line dsol ON dsol.order_id = dso.id
                WHERE 1=1
                AND dso.activity_plan_id = pal.id
                AND dso.state in ('progress','done')
            ) as actual_unit
            , l_s.complete_name as loc_src
            , tk.lat
            , tk.long
            FROM tw_activity_atl_btl pa
            INNER JOIN tw_activity_atl_btl_line pal ON pal.activity_id = pa.id
            INNER JOIN res_company b ON b.id = pa.company_id
            INNER JOIN tw_master_activity_type sp ON sp.id = pal.act_type_id
            INNER JOIN tw_mapping_titik_keramaian mtk ON mtk.id = pal.mapping_activity_id
            INNER JOIN tw_titik_keramaian tk ON tk.id = mtk.activity_point_id 
            INNER JOIN tw_ring tr ON tr.id = mtk.ring_id
            INNER JOIN res_district kec On kec.id = tk.district_id 
            LEFT JOIN res_sub_district kel ON kel.id = tk.sub_district_id
            LEFT JOIN res_city city ON city.id = kec.city_id
            left join tw_selection sc on sc.type = 'SalesChannel' and sc.id = pal.sales_channel_id 
            INNER JOIN hr_employee hr ON hr.id = pal.pic_id
            LEFT JOIN stock_location loc ON loc.id = pal.location_id
            LEFT JOIN stock_location l_s ON l_s.id = pal.source_pos_location_id 
            {query_where}
            ORDER BY b.code ASC
        """

        self._cr.execute(query)
        ress =  self._cr.dictfetchall()
        return self.env['web.report'].sudo().generate_report('Report Activity Plan',ress)

