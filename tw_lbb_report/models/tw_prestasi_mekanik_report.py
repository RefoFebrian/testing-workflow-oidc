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
class TwWPPReport(models.TransientModel):
    _inherit = "tw.lbb.report"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods

    def _print_excel_report_prestasi_mekanik(self):
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook = self.add_workbook_format(workbook)
        wbf=self.wbf

        date= self._get_default_date()
        date = date.strftime("%Y-%m-%d %H:%M:%S")
        file_name = 'Laporan Prestasi Mekanik'+str(date)+'.xlsx' 
        
        company_id = self.company_id.id  
        start_date = self.start_date.strftime("%Y-%m-%d")
        end_date = self.end_date.strftime("%Y-%m-%d")
        tz = '7 hours'
        
        query_where = ""
        query_group = "GROUP BY mechanic.name, wo.mechanic_id"
        query_order= " order by mechanic.name "
        
        if company_id :
            query_where += "  AND wo.company_id = '%s'" % str(company_id)
        if start_date :
            query_where += " AND wo.create_date >= '%s'" % str(start_date)
        if end_date :
            end_date = end_date + ' 23:59:59'
            query_where += " AND wo.create_date <= to_timestamp('%s', 'YYYY-MM-DD HH24:MI:SS') + interval '%s'" % (end_date,tz)
        
        query = f"""
            select
                coalesce(sales.name,
                '') as sales_name 
                        ,
                coalesce(wo_inv.cnt_kpb_1,
                0) as cnt_kpb_1
                        ,
                coalesce(wo_inv.cnt_kpb_2,
                0) as cnt_kpb_2
                        ,
                coalesce(wo_inv.cnt_kpb_3,
                0) as cnt_kpb_3
                        ,
                coalesce(wo_inv.cnt_kpb_4,
                0) as cnt_kpb_4
                        ,
                coalesce(wo_inv.cnt_cla,
                0) as cnt_cla
                        ,
                coalesce(wo_jasa.qty_cs,
                0) as qty_cs
                        ,
                coalesce(wo_jasa.qty_ls,
                0) as qty_ls
                        ,
                coalesce(wo_jasa.qty_or,
                0) as qty_or
                        ,
                coalesce(wo_jasa.qty_lr,
                0) as qty_lr
                        ,
                coalesce(wo_jasa.qty_hr,
                0) as qty_hr
                        ,
                coalesce(wo_inv.cnt_inv,
                0) as cnt_inv
                        ,
                coalesce(wo_unit.unit_entry,
                0) as unit_entry
                        ,
                coalesce(wo_inv.cnt_war,
                0) as cnt_war
                        ,
                coalesce(jam_terpakai.jam_terpakai,
                0) as jam_terpakai
                        ,
                -- TODO Uncomment jika sudah ada tw_attendance
                0 as total_tidak_masuk,
                0 as total_masuk
                --coalesce(absensi.absen,
                --0) as total_tidak_masuk
                --        ,
                --coalesce(absensi.total_masuk,
                --0) as total_masuk
            from
                (
                select
                    wo.mechanic_id
                        ,
                    wo.company_id
                        ,
                    COUNT(wo.id) as cnt_inv
                        ,
                    COUNT(case when type.value = 'KPB' and wo.kpb_ke = '1' then wo.id end) as cnt_kpb_1
                        ,
                    COUNT(case when type.value = 'KPB' and wo.kpb_ke = '2' then wo.id end) as cnt_kpb_2
                        ,
                    COUNT(case when type.value = 'KPB' and wo.kpb_ke = '3' then wo.id end) as cnt_kpb_3
                        ,
                    COUNT(case when type.value = 'KPB' and wo.kpb_ke = '4' then wo.id end) as cnt_kpb_4
                        ,
                    COUNT(case when type.value = 'CLA' then wo.id end) as cnt_cla
                        ,
                    COUNT(case when type.value = 'WAR' then wo.id end) as cnt_war
                from
                    tw_work_order wo
                left join tw_selection type on type.id = wo.type_id
                left join hr_employee as employee on
                    employee.id = wo.mechanic_id
                where
                    wo.company_id = {company_id}
                    and wo.create_date between '{start_date}' and '{end_date}'
                group by
                    wo.mechanic_id,
                    wo.company_id) as wo_inv
            full outer join
                        (
                select
                    company_id 
                        ,
                    mechanic_id
                        ,
                    SUM(cnt_per_date) as unit_entry
                from
                    (
                    select
                        wo.company_id,
                        wo.mechanic_id,
                        wo.create_date,
                        COUNT(distinct lot_id) as cnt_per_date
                    from
                        tw_work_order wo
                        left join tw_selection type on type.id = wo.type_id
                    where
                        type.value <> 'WAR'
                        and type.value <> 'SLS'
                        and wo.create_date between '{start_date}' and '{end_date}'
                    group by
                        wo.company_id,
                        wo.mechanic_id,
                        wo.create_date ) wo_per_date
                group by
                    company_id,
                    mechanic_id) as wo_unit
                        on
                wo_inv.company_id = wo_unit.company_id
                and wo_inv.mechanic_id = wo_unit.mechanic_id
            --full outer join
            --            (
            --    select
            --        branch.id as company_id,
            --        sales.user_id ,
            --        sum(jumlah_hari_kerja-total_absensi) absen,
            --        sum(total_absensi) total_masuk
            --    from
            --        tw_attendance as absensi
            --    left join hr_employee hr_sales on
            --        absensi.nip = hr_sales.nip
            --    left join resource_resource sales on
            --        sales.id = hr_sales.resource_id
            --    left join res_users as users on
            --        users.id = sales.user_id
            --    left join res_company as branch on
            --        branch.id = hr_sales.company_id
            --    where
            --        branch.id = {company_id}
            --        and absensi.bulan = '{start_date[:-3]}'
            --    group by
            --        branch.id,
            --        sales.user_id 
            --            
            --            
            --            ) as absensi
            --            on
            --    absensi.company_id = wo_unit.company_id
            --    and absensi.user_id = wo_unit.mechanic_id
            full outer join
                        (
                select
                    wo.company_id,
                    wo.mechanic_id
                        ,
                    date_part( 'epoch',
                    SUM(age(wo_start.finish_date, wo_start.start_date) )::interval )/ 3600 as jam_terpakai
                from
                    tw_work_order as wo
                left join tw_start_stop_wo as wo_start
                        on
                    wo.id = wo_start.work_order_id
                left join res_company as branch on
                    branch.id = wo.company_id
                where
                    1 = 1
                    and wo.create_date between '{start_date}' and '{end_date}'
                group by
                    wo.company_id,
                    wo.mechanic_id
                        
                        ) as jam_terpakai
                        on
                jam_terpakai.company_id = wo_unit.company_id
                and jam_terpakai.mechanic_id = wo_unit.mechanic_id
            full outer join
                        (
                select
                    wo.company_id,
                    wo.mechanic_id
                        ,
                    SUM(case when wol.division = 'Service' then wol.price_unit *(1-coalesce(wol.discount, 0)/ 100) end) amt_jasa
                        ,
                    SUM(case when wol.division = 'Sparepart' and pc.name not in ( 'OLI', 'OIL') then wol.price_unit *(1-coalesce(wol.discount, 0)/ 100) end) amt_part
                        ,
                    SUM(case when wol.division = 'Sparepart' and pc.name = 'OIL' then wol.price_unit *(1-coalesce(wol.discount, 0)/ 100) end) amt_oil
                        ,
                    SUM(wol.price_unit *(1-coalesce(wol.discount, 0)/ 100)) amt_total
                        ,
                    COUNT(case when wol.division = 'Service' and pc2.name = 'KPB' then wol.id end) qty_kpb
                        ,
                    COUNT(case when wol.division = 'Service' and pc.name = 'CS' then wol.id end) qty_cs
                        ,
                    COUNT(case when wol.division = 'Service' and pc.name = 'LS' then wol.id end) qty_ls
                        ,
                    COUNT(case when wol.division = 'Service' and pc.name = 'OR+' then wol.id end) qty_or
                        ,
                    COUNT(case when wol.division = 'Service' and pc2.name = 'QS' then wol.id end) qty_qs
                        ,
                    COUNT(case when wol.division = 'Service' and pc.name = 'LR' then wol.id end) qty_lr
                        ,
                    COUNT(case when wol.division = 'Service' and pc.name = 'HR' then wol.id end) qty_hr
                        ,
                    COUNT(case when wol.division = 'Service' and pc.name = 'CLA' then wol.id end) qty_cla
                        ,
                    COUNT(case when wol.division = 'Service' then wol.id end) qty_total
                from
                    tw_work_order wo
                inner join tw_work_order_line wol on
                    wo.id = wol.order_id
                left join product_product p on
                    wol.product_id = p.id
                left join product_template pt on
                    p.product_tmpl_id = pt.id
                left join product_category pc on
                    pt.categ_id = pc.id
                left join product_category pc2 on
                    pc.parent_id = pc2.id
                where
                    wo.create_date between '{start_date}' and '{end_date}'
                group by
                    wo.company_id,
                    wo.mechanic_id) as wo_jasa
                        on
                wo_inv.company_id = wo_jasa.company_id
                and wo_inv.mechanic_id = wo_jasa.mechanic_id
            inner join res_users users on
                users.id = coalesce( wo_inv.mechanic_id,
                coalesce(wo_unit.mechanic_id,
                wo_jasa.mechanic_id))
            inner join res_company c on
                c.id = coalesce(wo_inv.company_id,
                coalesce(wo_unit.company_id,
                wo_jasa.company_id))
            left join resource_resource sales on
                users.id = sales.user_id
            left join hr_employee hr_sales on
                sales.id = hr_sales.resource_id
            left join hr_job job on
                hr_sales.job_id = job.id
            where
                c.id = {company_id}
        """ 
        self._cr.execute (query)
        ress = self._cr.fetchall()

        worksheet = workbook.add_worksheet('PRESTASI MEKANIK')
        worksheet.set_column('A1:A1', 2)
        worksheet.set_column('B1:B1', 2)
        worksheet.set_column('C1:C1', 2)
        worksheet.set_column('D1:D1', 25)
        worksheet.set_column('E1:E1', 6)
        worksheet.set_column('F1:F1', 6)
        worksheet.set_column('G1:G1', 6)
        worksheet.set_column('H1:H1', 6)
        worksheet.set_column('I1:I1', 2)
        worksheet.set_column('I18:I18', 5)
        worksheet.set_column('J1:J1', 8)
        worksheet.set_column('J16:J16', 5)
        worksheet.set_column('K1:K1', 15)
        worksheet.set_column('K11:K11', 2)
        worksheet.set_column('K17:K17', 5)
        worksheet.set_column('L1:L1', 2)
        worksheet.set_column('L7:L7', 10)
        worksheet.set_column('L17:L17', 5)
        worksheet.set_column('M1:M1', 5)
        worksheet.set_column('M7:M7', 15)
        worksheet.set_column('M17:M17', 5)
        worksheet.set_column('N1:N1', 2)
        worksheet.set_column('N6:N6', 5)
        worksheet.set_column('O1:O1', 2)
        worksheet.set_column('O6:O6', 5)
        worksheet.set_column('P1:P1', 2)
        worksheet.set_column('P6:P6', 5)
        worksheet.set_column('Q1:Q1', 2)
        worksheet.set_column('Q7:Q7', 15)
        worksheet.set_column('Q8:Q8', 15)
        worksheet.set_column('Q9:Q9', 8)
        worksheet.set_column('Q10:Q10', 6)
        worksheet.set_column('R1:R1', 2)
        worksheet.set_column('R16:R16', 5)
        worksheet.set_column('S1:S1', 2)
        worksheet.set_column('S6:S6', 9)
        worksheet.set_column('T1:T1', 7 )
        worksheet.set_column('U1:U1', 7)
        worksheet.set_column('V1:V1', 9)
        worksheet.set_column('W1:W1', 7)
        worksheet.set_column('X1:X1', 20)
        worksheet.set_column('Y1:Y1', 20)
        worksheet.set_column('Z1:Z1', 20)
        worksheet.set_column('AA1:AA1', 8)
        worksheet.set_column('AB1:AB1', 8)
        worksheet.set_column('AC1:AC1', 20)
        worksheet.set_column('AD1:AD1', 20)      

        worksheet.merge_range('C%s:V%s' % (1,1), 'LAPORAN MEKANIK', wbf['title']) 
        worksheet.merge_range('C%s:V%s' % (4,4), 'III.   Laporan Prestasi Mekanik Dalam Bulan Ini %s s/d %s' %(str(start_date),str(end_date)), wbf['header_table_v_center_bold'])
        worksheet.merge_range('C%s:C%s' % (5,8), 'No', wbf['header_table_v_center'])
        worksheet.merge_range('D%s:D%s' % (5,8), 'NAMA MEKANIK', wbf['header_table_v_center_bold'])
        worksheet.merge_range('E%s:E%s' % (5,8), 'ABSEN \n (hari)', wbf['header_table_v_center_bold'])
        worksheet.merge_range('F%s:F%s' % (5,8), 'HADIR \n (hari)', wbf['header_table_v_center_bold'])
        worksheet.merge_range('G%s:G%s' % (5,8), 'P M T Ke \n (0/1/2/3)', wbf['header_table_v_center_bold'])
        worksheet.merge_range('H%s:H%s' % (5,8), 'Jumlah \n LKH', wbf['header_table_v_center_bold'])
        worksheet.merge_range('I%s:L%s' % (5,6), 'ASS', wbf['header_table_v_center_bold'])
        worksheet.merge_range('I%s:I%s' % (7,8), 'KPB1', wbf['header_table_v_center'])
        worksheet.merge_range('J%s:J%s' % (7,8), 'KPB2', wbf['header_table_v_center'])
        worksheet.merge_range('K%s:K%s' % (7,8), 'KPB3', wbf['header_table_v_center'])
        worksheet.merge_range('L%s:L%s' % (7,8), 'KPB4', wbf['header_table_v_center'])
        worksheet.merge_range('M%s:M%s' % (5,8), 'Claim \n C2', wbf['header_table_v_center_bold'])
        worksheet.merge_range('N%s:P%s' % (5,5), 'QS', wbf['header_table_v_center_bold'])
        worksheet.write('N8', 'CS' , wbf['header_table_v_center_bold'])
        worksheet.write('O8', 'LS' , wbf['header_table_v_center_bold'])
        worksheet.write('P8', 'OR +' , wbf['header_table_v_center_bold'])
        worksheet.merge_range('N%s:N%s' % (6,7), 'Paket \n Lengkap', wbf['header_table_v_center'])
        worksheet.merge_range('O%s:O%s' % (6,7), 'Paket \n Ringan', wbf['header_table_v_center'])
        worksheet.merge_range('P%s:P%s' % (6,7), 'Ganti \n Oli +', wbf['header_table_v_center'])
        worksheet.merge_range('Q%s:Q%s' % (5,8), 'LR \n Servis \n Ringan', wbf['header_table_v_center_bold'])
        worksheet.merge_range('R%s:R%s' % (5,8), 'HR \n Servis \n Berat', wbf['header_table_v_center_bold'])
        worksheet.merge_range('S%s:S%s' % (5,8), 'TOTAL \n PEKERJAAN', wbf['header_table_v_center_bold'])
        worksheet.merge_range('T%s:T%s' % (5,8), 'TOTAL \n UNIT', wbf['header_table_v_center_bold'])
        worksheet.merge_range('U%s:U%s' % (5,8), 'JR \n Pekerjaan \n Ulang', wbf['header_table_v_center_bold'])
        worksheet.merge_range('V%s:V%s' % (5,8), 'Jam Terpakai \n ( Menit )', wbf['header_table_v_center_bold'])
        row=8
        rowsaldo = row
        row+=1             
        no = 1  
        row1 = row
        
        grand_total_kpb1=0
        grand_total_kpb2=0
        grand_total_kpb3=0
        grand_total_kpb4=0
        grand_total_claim = 0
        grand_total_cs = 0
        grand_total_ls = 0
        grand_total_or = 0
        grand_total_lr = 0
        grand_total_hr = 0
        grand_total_pekerjaan = 0
        grand_total_unit = 0
        grand_total_jr = 0
        
        query_group_total = "GROUP BY wo.mechanic_id"
        for res in ress:
            nama_mekanik = str(res[0].encode('ascii','ignore').decode('ascii')) if res[0] != None else ''
            total_kpb1 = res[1]
            total_kpb2 = res[2]
            total_kpb3 = res[3]   
            total_kpb4 = res[4]
            total_claim = res[5]
            total_cs = res[6]
            total_ls = res[7]
            total_or = res[8]
            total_lr = res[9]
            total_hr = res[10]
            total_pekerjaan = res[11]
            total_unit = res[12]
            total_jr = res[13]
            jam_terpakai = res[14]
            total_tidak_masuk = res[15]
            total_masuk = res[16]
            
            worksheet.write('C%s' % row, no , wbf['content'])
            worksheet.write('D%s' % row, nama_mekanik , wbf['content'])
            worksheet.write('E%s' % row, total_tidak_masuk , wbf['content_float'])
            worksheet.write('F%s' % row, total_masuk , wbf['content_float'])
            worksheet.write('G%s' % row, '' , wbf['content_float'])
            worksheet.write('H%s' % row, '' , wbf['content_float'])
            worksheet.write('I%s' % row, total_kpb1 , wbf['content_float'])
            worksheet.write('J%s' % row, total_kpb2 , wbf['content_float'])
            worksheet.write('K%s' % row, total_kpb3 , wbf['content_float'])
            worksheet.write('L%s' % row, total_kpb4 , wbf['content_float'])
            worksheet.write('M%s' % row, total_claim , wbf['content_float'])
            worksheet.write('N%s' % row, total_cs , wbf['content_float'])
            worksheet.write('O%s' % row, total_ls , wbf['content_float'])
            worksheet.write('P%s' % row, total_or , wbf['content_float'])
            worksheet.write('Q%s' % row, total_lr , wbf['content_float'])
            worksheet.write('R%s' % row, total_hr , wbf['content_float'])
            worksheet.write('S%s' % row, total_pekerjaan , wbf['content_float'])
            worksheet.write('T%s' % row, total_unit , wbf['content_float'])
            worksheet.write('U%s' % row, total_jr , wbf['content_float'])
            worksheet.write('V%s' % row, str(jam_terpakai)+' Jam' , wbf['content'])
        
            no+=1
            row+=1
            
            grand_total_kpb1 += total_kpb1
            grand_total_kpb2 += total_kpb2
            grand_total_kpb3 += total_kpb3
            grand_total_kpb4 += total_kpb4
            grand_total_claim += total_claim
            grand_total_cs += total_cs
            grand_total_ls += total_ls
            grand_total_or += total_or
            grand_total_lr += total_lr
            grand_total_hr += total_hr
            grand_total_pekerjaan += total_pekerjaan
            grand_total_unit += total_unit
            grand_total_jr += total_jr
        
        worksheet.merge_range('C%s:D%s' % (row,row), 'TOTAL', wbf['content_total']) 
        worksheet.write('E%s' % row, '' , wbf['content_float_bold'])
        worksheet.write('F%s' % row, '' , wbf['content_float_bold'])
        worksheet.write('G%s' % row, '' , wbf['content_float_bold'])
        worksheet.write('H%s' % row, '' , wbf['content_float_bold'])
        worksheet.write('I%s' % row, grand_total_kpb1 , wbf['content_float_bold'])
        worksheet.write('J%s' % row, grand_total_kpb2 , wbf['content_float_bold'])
        worksheet.write('K%s' % row, grand_total_kpb3 , wbf['content_float_bold'])
        worksheet.write('L%s' % row, grand_total_kpb4 , wbf['content_float_bold'])
        worksheet.write('M%s' % row, grand_total_claim , wbf['content_float_bold'])
        worksheet.write('N%s' % row, grand_total_cs , wbf['content_float_bold'])
        worksheet.write('O%s' % row, grand_total_ls , wbf['content_float_bold'])
        worksheet.write('P%s' % row, grand_total_or , wbf['content_float_bold'])
        worksheet.write('Q%s' % row, grand_total_lr , wbf['content_float_bold'])
        worksheet.write('R%s' % row, grand_total_hr , wbf['content_float_bold'])
        worksheet.write('S%s' % row, grand_total_pekerjaan , wbf['content_float_bold'])
        worksheet.write('T%s' % row, grand_total_unit , wbf['content_float_bold'])
        worksheet.write('U%s' % row, grand_total_jr , wbf['content_float_bold'])
        worksheet.write('V%s' % row, '' , wbf['content_float_bold'])
            
        worksheet.merge_range('C%s:V%s' % (row+1,row+1), '    ASISTEN MEKANIK', wbf['header_table_v_bold']) 
        worksheet.write('C%s' % (row+2), 'No' , wbf['header_table_v_center'])
    
        for loop in range(1,4):
           worksheet.write('C%s' % (row+loop+2), loop , wbf['content'])
           worksheet.write('D%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('E%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('F%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('G%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('H%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('I%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('J%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('K%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('L%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('M%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('N%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('O%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('P%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('Q%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('R%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('S%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('T%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('U%s' % (row+loop+2) ,'', wbf['content'])
           worksheet.write('V%s' % (row+loop+2) ,'', wbf['content'])
           
        worksheet.merge_range('C%s:D%s' % (row+5,row+5), 'TOTAL', wbf['content_total'])   
        worksheet.merge_range('C%s:V%s' % (row+6,row+6), '    TURN OVER  MECHANIC (MEKANIK KELUAR)', wbf['header_table_v_bold'])  
  
        worksheet.write('C%s' % (row+7), 'No' , wbf['header_table_v_center'])
        worksheet.merge_range('D%s:G%s' % (row+7,row+7), 'N A M A    M  E  K  A  N  I  K', wbf['header_table_v_center'])  
        worksheet.merge_range('H%s:K%s' % (row+7,row+7), 'Bergabung Sejak Tanggal', wbf['header_table_v_center'])  
        worksheet.merge_range('L%s:O%s' % (row+7,row+7), 'Mengundurkan Diri Tanggal', wbf['header_table_v_center']) 
        worksheet.merge_range('P%s:V%s' % (row+7,row+7), 'Alasan Keluar', wbf['header_table_v_center'])
         
        for loop_2 in range(1,4):
            
            worksheet.write('C%s' % (row+loop_2+7), loop_2 , wbf['content'])
            worksheet.merge_range('D%s:G%s' % (row+loop_2+7,row+loop_2+7), '', wbf['content'])  
            worksheet.merge_range('H%s:K%s' % (row+loop_2+7,row+loop_2+7), '', wbf['content'])  
            worksheet.merge_range('L%s:O%s' % (row+loop_2+7,row+loop_2+7), '', wbf['content']) 
            worksheet.merge_range('P%s:V%s' % (row+loop_2+7,row+loop_2+7), '', wbf['content'])
        
        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        fp.close()
        report_id = self.env['web.report'].create({
            'report_file' : out,
            'name' : file_name,
        })
        return report_id, file_name