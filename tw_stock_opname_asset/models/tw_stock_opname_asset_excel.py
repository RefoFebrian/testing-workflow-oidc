from odoo import api, fields, models
from odoo.exceptions import UserError as Warning

from datetime import datetime


class TwStockOpanmeExcel(models.TransientModel):
    _name = "tw.stock.opname.asset.excel"
    _description = "TW Stock Opname Asset Excel"

    name = fields.Char(string="Name")
    
    stock_opname_asset_id = fields.Many2one('tw.stock.opname.asset', string="Stock Opname Asset")

    def action_import_excel(self):
        query_where = "WHERE 1=1 "
        if self.stock_opname_asset_id:
            query_where += " AND so_asset.id = {}".format(self.stock_opname_asset_id.id)
    

        query_so_asset = f"""
           SELECT 
            branch.code as Code ,
            branch.name as Cabang,
            tso.code as Kode_Aset,
            tso.name as Nama_Aset,
            tso.category as Kategory,
            tso.description as Kategory_Desc,
            tso.physical_validation as Validasi_Fisik,
            tso.asset_status as Status_Asset,
            tso.pic_validation_id as PIC_Asset,
            tso.physical_condition as Konidisi_Fisik_Asset,
            tso.engine_no as No_Engine,
            tso.description as Keterangan
            FROM tw_stock_opname_asset so_asset
            JOIN tw_stock_opname_asset_line tso ON tso.opname_id = so_asset.id
            LEFT JOIN res_company branch on branch.id = so_asset.company_id
            LEFT JOIN stock_location location ON location.id = tso.validation_location_id
            LEFT JOIN hr_employee employee ON employee.id = tso.pic_validation_id
            {query_where}
        """.format(query_where=query_where)

        self.env.cr.execute(query_so_asset)
        ress = self.env.cr.dictfetchall()
        if not ress:
            raise Warning('Tidak ada data.')


        query_asset_tidak_tercatat = f"""
           SELECT 
            branch.code as Code ,
            branch.name as Cabang,
            ts_other.name as name,
            ts_other.physical_location as Lokasi_Fisik_Unit,
            hr.name as PIC_Asset,
            ts_other.physical_condition as Kondisi_Fisik_Asset,
            ts_other.engine_no as No_Engine,
            ts_other.description as Keterangan
            FROM tw_stock_opname_asset so_asset
            JOIN tw_stock_opname_asset_other ts_other ON ts_other.opname_id = so_asset.id
            LEFT JOIN res_company branch on branch.id = so_asset.company_id
            LEFT JOIN hr_employee hr on hr.id = ts_other.pic_asset_id
            {query_where}
        """.format(query_where=query_where)

        self.env.cr.execute(query_asset_tidak_tercatat)
        new_ress = self.env.cr.dictfetchall()
        if not new_ress:
            new_ress = [{
                'Code': '',
                'Cabang': '',
                'name': '',
                'Lokasi_Fisik_Unit': '',
                'PIC_Asset': '',
                'Kondisi_Fisik_Asset': '',
                'No_Engine': '',
                'Keterangan': 'Tidak ada data.'
            }]

        data_sheet = {'Stock Opname Asset': ress, 'Asset Tidak Tercatat': new_ress}
        return self.env['web.report'].generate_report('Stock Opname Asset', ress, data_sheet=data_sheet)