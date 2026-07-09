from odoo import models, fields
from odoo.exceptions import UserError as Warning


class DownloadStpckOpname (models.TransientModel):
    _name = "tw.stock.opname.download"
    _description = "Download Stock Opname Download Detail"

    name = fields.Char('Filename')
    data_file = fields.Binary('File')

    def action_download_detail(self, opname_id, division, state=None):
        where = ""
        select = ""
        join = ""
        group = ""

        if state == 'open':
            where += " AND detail.state in ('selisih','anomali')"
            
        if division == self.env.ref('tw_selection.selection_unit_division').id:
            select += ", loc_stock.name lokasi"
            join += "LEFT JOIN stock_location loc_stock ON loc_stock.id = detail.location_id"
            group += "GROUP BY loc_stock.name,users.nip, opname.name, opname.periode_awal, opname.periode_akhir"
            
        elif division == self.env.ref('tw_selection.selection_sparepart_division').id:
            select += ", sl.name lokasi"
            join += "LEFT JOIN stock_location sl ON sl.id = detail.location_id"
            group += "GROUP BY sl.name, users.nip, opname.name, opname.periode_awal, opname.periode_akhir"

        query = f"""
           SELECT opname.name as no_stock_opname
                {select}
                , count(detail.product_code) as total_product
                , users.nip as pic
                , opname.periode_awal::DATE || ' s/d ' || opname.periode_akhir::DATE as periode
            FROM tw_stock_opname_detail detail
            LEFT JOIN hr_employee users ON detail.employee_id = users.id
            LEFT JOIN tw_stock_opname opname ON opname.id = detail.opname_id
            {join}
            WHERE 1=1
            AND detail.employee_id isnull
            AND opname.id = {opname_id}
            AND opname.division = {division}
            {where}
            {group}
        """
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        if not result:
            raise Warning('Data tidak ada!')
        
        return self.env['tw.report'].generate_report('Detail Stock Opname', result)