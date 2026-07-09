import pytz
from datetime import datetime
from odoo import models, fields, api, _
from odoo.http import request
import io
import base64
from PyPDF2 import PdfFileMerger
from odoo.exceptions import UserError as Warning


class PrintBusinessTrip(models.AbstractModel):
    _name = "report.tw_business_trip.print_business_trip_pdf"
    _description = "Print Business Trip PDF"

    def _get_approval(self, docs):
        business_trip_id = docs.id
        business_model_id = self.env['ir.model'].sudo().search([('model', '=', 'tw.business.trip')], limit=1).id
        query = """
        SELECT DISTINCT ON (result."limit") * FROM (
            SELECT DISTINCT ON (al.limit)
                al.limit,
                p.name AS approved_by,
                he.name,
                ttd.filename_upload_foto AS filename_ttd,
                COALESCE(hd.complete_name, '') AS department_name,
                rg.name->>'en_US' AS group_name,
                'APPROVED BY SYSTEM' AS approved_st
            FROM tw_approval_line al
            JOIN res_users u ON al.approver_id = u.id
            JOIN res_partner p ON u.partner_id = p.id
            JOIN resource_resource rr ON rr.user_id = u.id
            LEFT JOIN hr_employee he ON he.resource_id = rr.id
            LEFT JOIN hr_department hd ON hd.id = he.department_id
            LEFT JOIN tw_master_ttd ttd ON ttd.employee_id = he.id
            LEFT JOIN res_groups rg ON rg.id = al.group_id 
            JOIN tw_business_trip pd ON pd.id = al.transaction_id
            WHERE al.model_id = {model_id} AND al.transaction_id = {trx_id} AND al.state = 'approve'
            UNION ALL
            SELECT
                '0' AS limit,
                he.name AS approved_by,
                he.name,
                ttd.filename_upload_foto AS filename_ttd,
                COALESCE(hd.complete_name, '') AS department_name,
                concat(hd.complete_name, ' - Pemohon') AS group_name,
                'APPROVED BY SYSTEM' AS approved_st
            FROM tw_business_trip pd
            LEFT JOIN hr_employee he ON he.id = pd.pic_id
            LEFT JOIN hr_department hd ON hd.id = he.department_id
            LEFT JOIN tw_master_ttd ttd ON ttd.employee_id = he.id
            WHERE pd.id = {trx_id}
        ) AS result
        ORDER BY "limit";
        """.format(model_id=business_model_id, trx_id=business_trip_id)

        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()

        for res in result:
            ttd_file = False
            filename_ttd = res.get('filename_ttd')

            if filename_ttd:
                file = self.env['tw.config.files'].suspend_security().get_file(filename_ttd)
                if file:
                    ttd_file = file.decode('utf-8')

            res["ttd_file_foto"] = ttd_file
            # if not res.get('filename_ttd'):
            #     raise Warning("Tanda tangan {name} belum ada di master".format(name=res.get("name")))

            # file = self.env['tw.config.files'].suspend_security().get_file(res.get('filename_ttd'))
            # if not file:
            #     raise Warning("File tanda tangan {name} tidak di temukan, harap upload ulang tanda tangan".format(name=res.get("name")))

            # res["ttd_file_foto"] = file.decode('utf-8')

        return result
    
    def _get_manager_pic(self, docs):
        business_trip_id = docs.id
        query = """
            SELECT manager.name as name
                , ttd.filename_upload_foto AS filename_ttd
                , job.name->>'en_US' AS job_title
            FROM tw_business_trip pd
            LEFT JOIN hr_employee pic ON pic.id = pd.pic_id
            LEFT JOIN hr_department hd ON hd.id = pic.department_id
            LEFT JOIN hr_employee manager ON hd.manager_id = manager.id
            LEFT JOIN hr_job job ON job.id = manager.job_id 
            LEFT JOIN tw_master_ttd ttd ON ttd.employee_id = manager.id
            WHERE pd.id = {trx} 
            LIMIT 1
        """.format(trx=business_trip_id)
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchone()

        ttd_file = False
        filename_ttd = result.get('filename_ttd')

        if filename_ttd:
            file = self.env['tw.config.files'].suspend_security().get_file(filename_ttd)
            if file:
                ttd_file = file.decode('utf-8')

        result["ttd_file_foto"] = ttd_file
        # if not result:
        #     raise Warning("Data Perjalanan Dinas tidak ditemukan")

        # if not result.get('filename_ttd'):
        #     raise Warning("Tanda tangan manager belum ada di master")

        # file = self.env['tw.config.files'].suspend_security().get_file(result.get('filename_ttd'))
        # if not file:
        #     raise Warning("File tanda tangan manager tidak di temukan, harap upload ulang tanda tangan")

        # result["ttd_file_foto"] = file.decode('utf-8')

        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.business.trip'].browse(data['id'])
        
        cost_breakdown = {}
        for doc in docs:
            costs = []

            for transport in doc.transportation_line_ids:
                costs.append({
                    'name': dict(self.env['tw.business.trip.transport']._fields['transportation'].selection).get(transport.transportation),
                    'cost_planning': transport.planning_cost,
                    'cost_actual': transport.actual_cost,
                    'cost_selisih': transport.selisih_cost,
                    'count_planning': 1,
                    'count_actual': 1
                })

            costs.append({
                'name': 'Uang makan / Saku',
                'cost_planning': doc.planning_food_cost,
                'cost_actual': doc.actual_food_cost,
                'cost_selisih': doc.selisih_food_cost,
                'count_planning': doc.planning_food_days,
                'count_actual': doc.actual_food_days
            })

            costs.append({
                'name': 'Akomodasi / Penginapan',
                'cost_planning': doc.planning_accommodation_cost,
                'cost_actual': doc.actual_accommodation_cost,
                'cost_selisih': doc.selisih_accommodation_cost,
                'count_planning': doc.planning_accommodation_days,
                'count_actual': doc.actual_accommodation_days
            })

            cost_breakdown[doc.id] = costs

        return {
            'docs': docs,
            'user': self.env.user,
            'cost_breakdown': cost_breakdown,
            'approval': self._get_approval(docs),
            'manager': self._get_manager_pic(docs),
        }
