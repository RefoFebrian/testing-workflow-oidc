from odoo import models
from odoo.exceptions import UserError


class TwStockOpnameExcelReport(models.Model):
    _inherit = "tw.vehicle.document.stock.opname"

    def action_download_excel_bpkb(self):
        self.ensure_one()

        query_sheet1 = f"""
            SELECT
                rc.code AS "Branch Code",
                rc.name AS "Branch Name",
                rp.name AS "Nama BPKB",
                line.validation_name_ownership AS "Validasi Nama BPKB",
                line.date_receipt AS "Tanggal Penerimaan",
                line.location_ownership AS "Lokasi BPKB",
                spl.name AS "No Engine",
                line.validation_no_engine_ownership AS "Validasi No Engine",
                line.ownership_number AS "No BPKB",
                line.validation_no_ownership AS "Validasi No BPKB",
                line.validation_check_physical_ownership AS "Ceklis Fisik BPKB",
                finco.name AS "Finance Company",
                line.description AS "Keterangan",
                line.age AS "Umur",
                line.over_due AS "Over Due"
            FROM
                tw_vehicle_document_stock_opname_line AS line
            JOIN
                tw_vehicle_document_stock_opname AS opname ON line.opname_id = opname.id
            JOIN
                res_company AS rc ON opname.company_id = rc.id
            LEFT JOIN
                res_partner AS rp ON line.customer_ownership_id = rp.id
            LEFT JOIN
                stock_lot AS spl ON line.lot_id = spl.id
            LEFT JOIN
                res_partner AS finco ON line.finco_id = finco.id
            WHERE
                line.opname_id = {self.id}
        """
        self.env.cr.execute(query_sheet1)
        sheet1_data = self.env.cr.dictfetchall()

        query_sheet2 = f"""
            SELECT
                rc.code AS "Branch Code",
                rc.name AS "Branch Name",
                other.name_ownership AS "Nama BPKB",
                other.no_engine AS "No Engine",
                other.description AS "Keterangan"
            FROM
                tw_vehicle_document_stock_opname_other AS other
            JOIN
                tw_vehicle_document_stock_opname AS opname ON other.opname_id = opname.id
            JOIN
                res_company AS rc ON opname.company_id = rc.id
            WHERE
                other.opname_id = {self.id}
        """
        self.env.cr.execute(query_sheet2)
        sheet2_data = self.env.cr.dictfetchall()

        data_sheet = {}
        if sheet1_data:
            data_sheet["Stock Opname BPKB"] = sheet1_data
        if sheet2_data:
            data_sheet["Stock Opname BPKB Other"] = sheet2_data

        if not data_sheet:
            raise UserError("Tidak ada data untuk dicetak.")

        primary_data = sheet1_data if sheet1_data else sheet2_data

        summary_header = {
            "A1": "No. Ref",
            "B1": self.name,
        }

        return self.env['web.report'].sudo().generate_report("Stock Opname BPKB", data=primary_data, data_sheet=data_sheet, data_summary_header=summary_header, show_total_footer=False,)

    def action_download_excel_stnk(self):
        self.ensure_one()

        query_sheet1 = f"""
            SELECT
                rc.code AS "Branch Code",
                rc.name AS "Branch Name",
                rp.name AS "Nama STNK",
                line.validation_name_registration AS "Validasi Nama STNK",
                line.date_receipt AS "Tanggal Penerimaan",
                line.location_registration AS "Lokasi STNK",
                spl.name AS "No Engine",
                line.validation_no_engine_registration AS "Validasi No Engine",
                line.plate_number AS "No Polisi",
                line.validation_plate_number AS "Validasi No Polisi",
                line.validation_check_physical_registration AS "Ceklis Fisik STNK",
                line.description AS "Keterangan",
                line.age AS "Umur"
            FROM
                tw_vehicle_document_stock_opname_line AS line
            JOIN
                tw_vehicle_document_stock_opname AS opname ON line.opname_id = opname.id
            JOIN
                res_company AS rc ON opname.company_id = rc.id
            LEFT JOIN
                res_partner AS rp ON line.customer_registration_id = rp.id
            LEFT JOIN
                stock_lot AS spl ON line.lot_id = spl.id
            WHERE
                line.opname_id = {self.id}
        """
        self.env.cr.execute(query_sheet1)
        sheet1_data = self.env.cr.dictfetchall()

        query_sheet2 = f"""
            SELECT
                rc.code AS "Branch Code",
                rc.name AS "Branch Name",
                other.name_registration AS "Nama STNK",
                other.no_engine AS "No Engine",
                other.description AS "Keterangan"
            FROM
                tw_vehicle_document_stock_opname_other AS other
            JOIN
                tw_vehicle_document_stock_opname AS opname ON other.opname_id = opname.id
            JOIN
                res_company AS rc ON opname.company_id = rc.id
            WHERE
                other.opname_id = {self.id}
        """
        self.env.cr.execute(query_sheet2)
        sheet2_data = self.env.cr.dictfetchall()

        data_sheet = {}
        if sheet1_data:
            data_sheet["Stock Opname STNK"] = sheet1_data
        if sheet2_data:
            data_sheet["Stock Opname STNK Other"] = sheet2_data

        if not data_sheet:
            raise UserError("Tidak ada data untuk dicetak.")

        primary_data = sheet1_data if sheet1_data else sheet2_data

        summary_header = {
            "A1": "No. Ref",
            "B1": self.name,
        }

        return self.env['web.report'].sudo().generate_report("Stock Opname STNK", data=primary_data, data_sheet=data_sheet, data_summary_header=summary_header, show_total_footer=False,)