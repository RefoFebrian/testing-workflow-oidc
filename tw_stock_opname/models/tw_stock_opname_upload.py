import base64
import xlrd

from datetime import datetime
from odoo import models, fields, _
from odoo.exceptions import UserError as Warning


class UploadStockOpname(models.TransientModel):
    _name = "tw.stock.opname.upload"
    _description = "Upload Stock Opname"

    def _get_default_datetime(self):
        return datetime.now()

    file = fields.Binary('File')
    date = fields.Date('Tanggal',readonly=True,default=_get_default_datetime)
    state_x = fields.Selection([('choose','choose'),('get','get')],default='choose')
    opname_id = fields.Many2one('tw.stock.opname', ondelete="cascade") 

    def get_detail(self, lokasi, opname_id=None):
        where = ""
        join=""
        if self.opname_id.division == 'Sparepart':
            join += "LEFT JOIN stock_location sl ON sl.id = detail.location_id"
            where += f"""
                AND sl.name = '{lokasi}'
                AND detail.opname_id = {self.opname_id.id}
            """
        else :
            join += "LEFT JOIN stock_location stock_loc ON stock_loc.id = detail.location_id"
            where += f"""
                AND stock_loc.id = {lokasi}
                AND detail.opname_id = {opname_id}
            """
            
        query = f"""
            SELECT json_agg(distinct detail.id) id
            FROM tw_stock_opname_detail detail
            {join}
            WHERE detail.employee_id is null
            {where}
        """
        self._cr.execute(query)
        return self._cr.dictfetchall()

    def get_detail_accessories(self, lokasi, opname_id=None):
        where = ""
        join=""
        join += "LEFT JOIN stock_location stock_loc ON stock_loc.id = detail.location_id"
        where += f"""
            AND stock_loc.id = {lokasi}
            AND detail.opname_id = {opname_id}
        """
            
        query = f"""
            SELECT json_agg(distinct detail.id) id
            FROM tw_stock_opname_accessories detail
            {join}
            WHERE detail.employee_id is null
            {where}
        """
        self._cr.execute(query)
        return self._cr.dictfetchall()

    def action_import(self):
        if not self.file:
            raise Warning('Silahkan input file terlebih dahulu.')
        
        opname_id = self.opname_id.id
        periode_awal = (self.opname_id.periode_awal).strftime("%Y-%m-%d")
        periode_akhir = (self.opname_id.periode_akhir).strftime("%Y-%m-%d")

        data = base64.decodestring(self.file)
        excel = xlrd.open_workbook(file_contents = data)
        sh = excel.sheet_by_index(0)

        warning_note = ''
        detail_so = []
        for rx in range(1, sh.nrows):
            values = [sh.cell(rx, ry).value for ry in range(sh.ncols)]
            lokasi = values[2]
            pic = str(values[4])

            fields = []
            if not pic:
                fields.append('pic')

            if len(fields) > 0:
                warning_note += ("Terdapat kolom kosong di baris %s -> pada lokasi %s!\n" %(rx, lokasi))

            if pic:
                employee_obj = self.env['hr.employee'].suspend_security().search([
                    ('nip','=',str(pic)),
                    ('active','=',True),
                    ('user_id','!=',False),
                    ],limit=1)
                if employee_obj:
                    query_check_pic = f"""
                        SELECT opname.name as no_so
                        FROM tw_stock_opname opname
                        LEFT JOIN tw_stock_opname_detail detail on detail.opname_id = opname.id
                        WHERE (
                            (opname.periode_awal BETWEEN '{periode_awal}' AND '{periode_akhir}')
                            OR (opname.periode_akhir BETWEEN '{periode_awal}' AND '{periode_akhir}')
                        )
                        AND detail.employee_id = {employee_obj.id}
                        AND opname.id != {opname_id}
                        LIMIT 1
                    """

                    self._cr.execute(query_check_pic)
                    check_pic = self._cr.dictfetchall()
                    
                    if check_pic :
                        raise Warning("PIC %s dalam transaksi %s. \nTidak dapat melakukan transaksi SO secara bersama dalam satu periode." %(employee_obj.name, check_pic[0]['no_so']))

                    detail_id = self.get_detail(lokasi)
                    detail_id = tuple(detail_id[0]['id'])

                    detail_so.append([1, detail_id, { 'employee_id': employee_obj.id }])
                else:
                    warning_note += ('Baris ke %s NIP %s tidak ditemukan\n' %(rx, pic))
        
        if warning_note:
            raise Warning(warning_note)

        vals = {
            'detail_opname_ids' : detail_so,
            'confirm_uid': self._uid,
            'confirm_date': self._get_default_datetime()
        }

        if self.opname_id.state == 'recount':
            vals.update({ 'state':'recount' })
        else:
            vals.update({ 'state':'in_progress' })

        self.opname_id.write(vals)
