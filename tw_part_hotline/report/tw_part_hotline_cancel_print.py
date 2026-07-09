from odoo import models, fields, api

class PrintDocumentCancelHotline(models.AbstractModel):
    _name = "report.tw_part_hotline.tw_part_hotline_cancel_print"
    _description = "TW Part Hotline Cancel Print"

    @api.model
    def render_html(self, docids, data=None):
        self.model = data.get('model')
        docs = self.env[self.model].browse(data['id'])
        self.no = 0
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'user': self._uid,
            'Date': fields.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return self.env['report'].render('tw_part_hotline.tw_part_hotline_cancel_print', docargs)