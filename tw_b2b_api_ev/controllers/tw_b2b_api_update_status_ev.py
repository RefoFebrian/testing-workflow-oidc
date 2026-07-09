# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
import requests
import json

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

# 4:  imports from odoo modules
import logging
_logger = logging.getLogger(__name__)

# 5: local imports

# 6: Import of unknown third party lib

class TWB2BApiUpdateStatusEV(models.Model):
    _inherit = "tw.b2b.api.ev"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def scheduler_post_acc_update_status(self,limit=100):
        config = self.env['tw.api.configuration'].suspend_security().search([('api_type_id.value','=','ahm')],limit=1)
        if not config:
            log_description = 'ERROR EV : Configuration Rest API belum di setting !'
            _logger.error(log_description)
            raise Warning(log_description)

        body = []
        end_point = '/jx05/ahmsvsdeve000-pst/rest/sd/eve012/acc-update-status'
        b2b_api_line_obj = self.env['tw.b2b.api.ev.line'].suspend_security().search([
            ('b2b_api_ev_id.state','=','done'),
            ('actual_ev_md_receive_date','=',False)
        ],limit=limit)

        serial_number_ids = [rec.serial_number for rec in b2b_api_line_obj]
        lot_obj = self.env['stock.lot'].suspend_security().search([('name','in',serial_number_ids)])
        for lot in lot_obj:
            accType = 'B' if lot.category_acc == 'EVBT' else 'C' if lot.category_acc == 'EVCH' else False
            receive_date = datetime.strptime(lot.receive_date,"%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)
            body.append({
                "serialNo": str(lot.name),
                "accType": accType,
                "accStatus": "2",
                "mdReceiveDate": receive_date.strftime("%Y-%m-%d %H:%M:%S"),
                "mdSLDate": "", "mdSLNo": "", "dealerCode": "", "dealerReceiveDate": "",
                "bastNo": "", "bastDate": "", "frameNo": "", "engineNo": "",
                "phoneNo": "", "custName": "", "invDirectSalesDate": "", "invDirectSalesNo": ""
            })

        try:
            status_code, content = config.proses_send_data_to_ahm_portal(url_proses_data=end_point, data=body)
            content = json.loads(content)

            log_vals = {
                'url': end_point,
                'request': body,
                'response_code': status_code,
                'response': content,
                # 'type': 'outgoing',
                # 'request_type': 'post',
                # 'jml_data': content.get('message', {}).get('rowCount', len(body))
            }

            if content.get('status') == '1':
                log_vals['name'] = 'Success Sending Status Accessories EV MD to AHM'
                lot_obj.suspend_security().write({'actual_ev_md_receive_date': datetime.now()})
            else:
                if 'data' in content:
                    for response in content.get('data'):
                        error_msg = response.get('errorMsg')
                        serial_no = response.get('serialNo')

                        error_text = error_msg[0] if isinstance(error_msg, list) and error_msg else 'Unknown Error'
                        serial_no = serial_no or 'UNKNOWN_SERIAL'
                        lot_obj = self.env['stock.lot'].suspend_security().search([('name','=',serial_no)])
                        lot_obj.suspend_security().write({'note_api_ev': error_text, 'actual_ev_md_receive_date': False})
                else:
                    lot_obj.suspend_security().write({'note_api_ev': 'Gagal Kirim', 'actual_ev_md_receive_date': False})
                log_vals['name'] = 'Data Accessories EV has been reject by AHM'
            self.env['tw.api.log'].sudo().create(log_vals)

        except Exception as e:
            message = 'Error Exception - %s'%(str(e))
            _logger.error(message)
            self.env['tw.api.log'].sudo().create({
                'name':'Failed Sending Status Accessories EV MD to AHM',
                'url':end_point,
                'request':body,
                'response_code':500, 
                'response':message,
                # 'type':'outgoing',
                # 'request_type':'post',
                # 'jml_data':len(body)
            })