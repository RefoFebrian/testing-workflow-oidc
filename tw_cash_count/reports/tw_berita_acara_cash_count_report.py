# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class tw_cash_count_print_berita_acara_report(models.AbstractModel):
    _name = "report.tw_cash_count.tw_cash_count_print_berita_acara"
    _description = "Cash Count Berita Acara Report"
    
    def no_urut(self):
        if not hasattr(self, 'no'):
            no = 0
        no += 1
        return no

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.cash.count'].browse(data['ids'])

        return {
            'doc_ids': docids,
            'doc_model': 'tw.cash.count',
            'data': data['form'],
            'docs': docs,
            'company_id': self.env.company[0],
            'user':data['user'],
            'date': fields.datetime.now().isoformat(),
            'no_urut': self.no_urut,
        }

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': self.process_data(),
            'docs': docs,
            'company_id': docs.company_id,
            'user':data['user'],
            'date': fields.datetime.now().isoformat(),
        }
        return self.env['report'].render('tw_cash_count.tw_cash_count_print_berita_acara', docargs)
