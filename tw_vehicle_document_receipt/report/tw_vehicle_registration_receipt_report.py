from odoo import models, api, _
from datetime import datetime
import pytz

class TwVehicleRegistrationReceiptReport(models.AbstractModel):
    _name = "report.tw_vehicle_document_receipt.reg_receipt_report"
    _description = "Vehicle Registration Receipt"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.vehicle.registration.receipt'].suspend_security().browse(docids)

        def default_local_time():
            menit = datetime.now()
            user = self.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            start = pytz.utc.localize(menit).astimezone(tz)
            return start.strftime("%d-%m-%Y %H:%M")

        def number_of_prints(doc_id):
            Model = self.env['ir.model']
            model_record = Model.search([('model', '=', 'tw.vehicle.registration.receipt')], limit=1)
            if not model_record:
                return 1

            Report = self.env['ir.actions.report']
            report_name = 'tw_vehicle_document_receipt.reg_receipt_report'
            report_record = Report.search([('report_name', '=', report_name)], limit=1)
            if not report_record:
                return 1

            JumlahCetak = self.env['tw.print.counter']
            
            tracking_record = JumlahCetak.search([
                ('report_id', '=', report_record.id),
                ('model_id', '=', model_record.id),
                ('transaction_id', '=', doc_id),
            ], limit=1)

            if not tracking_record:
                JumlahCetak.create({
                    'model_id': model_record.id,
                    'transaction_id': doc_id,
                    'print_counter': 1,
                    'report_id': report_record.id,
                })
                print_counter = 1
            else:
                print_counter = tracking_record.print_counter + 1
                tracking_record.write({'print_counter': print_counter})
                
            return print_counter

        return {
            'doc_ids': docids,
            'doc_model': 'tw.vehicle.registration.receipt',
            'docs': docs,
            'local_time': default_local_time,
            'print_counter': number_of_prints,
        }