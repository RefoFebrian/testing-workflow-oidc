from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse

import pytz

class PrintActivityATLBTL(models.AbstractModel):
    _name = "report.tw_activity_atl_btl.tw_activity_atl_btl_print"
    _description = "Print Activity ATL BTL"

    no = fields.Integer('no')
    
    def no_urut(self):
        if not hasattr(self, 'no'):
            self.no = 0
        self.no += 1
        return self.no

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.activity.atl.btl'].browse(docids) 
        self.no = 0

        return {
            'doc_ids': docids,
            'doc_model': 'tw.activity.atl.btl', 
            'docs': docs,
            'detail_ids': data.get('detail_ids', []),
            'branch': data.get('company_id'),
            'periode': data.get('periode'),
            'no_urut': self.no_urut(),
            'total_biaya_tdm': data.get('total_biaya_tdm'),
            'total_biaya_leasing': data.get('total_biaya_leasing'),
            'total_biaya_tdm_ppn': data.get('total_biaya_tdm_ppn'),
            'total_biaya_leasing_ppn': data.get('total_biaya_leasing_ppn'),
            'create_uid': data.get('create_uid'),
            'create_date': data.get('create_date'),
            'approved_uid': data.get('approved_uid'),
            'approved_date': data.get('approved_date'),
            'open_uid': data.get('open_uid'),
            'open_date': data.get('open_date'),
        }