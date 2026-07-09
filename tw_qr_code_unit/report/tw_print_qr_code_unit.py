from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse

import pytz
import qrcode
import base64
import io

class PrintQrCodeUnit(models.AbstractModel):
    _name = "report.tw_qr_code_unit.tw_print_qr_code_unit_template"
    _description = "Print QR Code Unit"
    
    @api.model
    def _get_report_values(self, docids, data=None):
        print_obj = self.env['tw.print.generate.qr.code.line'].suspend_security().search([('print_qr_code_id','=',data.get('id'))])
        # Generate QR codes and convert to base64
        for rec in print_obj:
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
            qr.add_data(rec.name)
            qr.make()
            img = qr.make_image(fill='black', back_color='white')

            # Save QR image as base64
            qr_buffer = io.BytesIO()
            img.save(qr_buffer, 'PNG')
            qr_buffer.seek(0)
            if rec.qr_code_id.state == 'New' :
                rec.qr_code_id.sudo().write({
                    'qr_code_base64': base64.b64encode(qr_buffer.read()).decode(),
                    'state': 'Printed',
                    'printed_date': datetime.now(),
                    'printed_uid': data.get('user')
                    })
        
        return {
            'doc_ids': docids,
            'doc_model': 'tw.print.generate.qr.code',
            'docs': print_obj
        }