from odoo import models, fields, api, _
from xlsxwriter.utility import xl_rowcol_to_cell
from odoo.exceptions import UserError as Warning
from datetime import datetime, timedelta

class StockOpnameReport(models.TransientModel):
    _name = "tw.stock.opname.report"
    _description = "Stock Opname Report"
    
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    file = fields.Char('File Name')
    data_x = fields.Binary('File', readonly=True)
    state_x =  fields.Selection([('choose','choose'),('get','get')],default='choose')
    status = fields.Selection([('in_progress','In Progress'),('final','Final')], string='Status', default='in_progress')
    start_date = fields.Date('Start Date',default=_get_default_date)
    end_date = fields.Date('End Date',default=_get_default_date)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    def excel_laporan(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self._download_laporan()
    
    def _download_laporan(self):
        additional_where = f" AND opname.division = '{self.division}'"
        select = ''

        if self.status == 'in_progress':
            additional_where += " AND opname.state in ('in_progress','recount')"
            select += """  SELECT opname.name AS no_stock_opname
                        , employee.name as nama_petugas
                        , opname.type_so AS tipe_perhitungan
                        , to_char(detail.count_date + INTERVAL '7 hours', 'DD/MM/YYYY HH24:MI:SS') as submit_time
                        , sl.name as location
                        , detail.product_code part_code
                        , tmpl.name::jsonb->>'en_US' as part_name
                        , detail.qty_count as qty_hasil_hitung
                        , detail.qty_system as qty_master
                        , detail.selisih
                        , detail.price * detail.qty_system amount_system
                        , detail.price * detail.qty_count amount_fisik
                        , COALESCE(detail.price * detail.selisih, 0) amount_selisih
                        , CASE
                            WHEN detail.selisih < 0 AND detail.state = 'selisih' THEN
                                    'Selisih Kurang'
                            WHEN detail.selisih > 0 AND detail.state = 'selisih' THEN
                                    'Selisih Lebih'
                            ELSE
                                INITCAP(detail.state)
                        END as keterangan_selisih  """
            title = 'Report Stock Opname Work In Progress'
        else:
            additional_where += " AND opname.state = 'done'"
            select += """
            SELECT opname.name AS no_stock_opname
                , sl.name as location
                , to_char(opname.periode_awal, 'DD/MM/YYYY') || ' s/d ' || to_char(opname.periode_akhir,  'DD/MM/YYYY') date
                , detail.product_code part_code
                , opname.type_so AS tipe_perhitungan
                , tmpl.name::jsonb->>'en_US' as part_name
                , '-' as kategori
                , '-' as subcategory
                , detail.qty_count as stock_system
                , detail.qty_system as fisik_hasil_hitung
                , 0 as not_good
                , detail.qty_count - 0 as total_fisik
                , detail.selisih
                , detail.price harga
                , COALESCE(detail.price * detail.qty_system, 0) amount_system
                , COALESCE(detail.price * detail.qty_count, 0) amount_fisik
                , COALESCE(detail.price * detail.selisih, 0) amount_selisih
                , CASE
                    WHEN detail.selisih < 0 AND detail.state = 'selisih' THEN
                            'Selisih Kurang'
                    WHEN detail.selisih > 0 AND detail.state = 'selisih' THEN
                            'Selisih Lebih'
                    ELSE
                        INITCAP(detail.state)
                END as keterangan_selisih
            """
            title = 'Report Hasil Stock Opname Final'
        query = f"""
                {select}
                FROM tw_stock_opname opname
                LEFT JOIN tw_stock_opname_detail detail ON detail.opname_id = opname.id
                LEFT JOIN stock_location sl ON sl.id = detail.location_id
                LEFT JOIN hr_employee employee ON employee.id = detail.employee_id
                LEFT JOIN product_product product ON product.id = detail.product_id
                LEFT JOIN product_template tmpl ON tmpl.id = product.product_tmpl_id
                WHERE 1=1
                AND (
                    (opname.periode_awal BETWEEN '{self.start_date}' AND '{self.end_date}')
                    OR (opname.periode_akhir BETWEEN '{self.start_date}' AND '{self.end_date}')
                    )
                {additional_where}
            """
        
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        if not ress:
            raise Warning("Tidak ada data.")
        
        return self.env['web.report'].generate_report(title,ress)
    