# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date
import base64


# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command
from odoo.modules.module import get_resource_path

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class PrintBarcodeLabelAsset(models.AbstractModel):
    _name = "report.tw_asset_barcode.print_barcode_label_asset"
    _description = "Print Barcode Label Asset"
    
    def time_date(self, date):
        return date.strftime("%d-%m-%Y %H:%M")

    def _lines(self, data):
        label_ids = data.get('label_asset_ids')
        report_id = self.env.ref('tw_asset_barcode.action_print_barcode_label_asset').id
        model_id = self.env['ir.model'].suspend_security().search([('model','=','account.asset.asset')]).id
        
        query = """
            SELECT lbl.asset_code AS category
                , lbll.asset_name AS name
                , lbll.asset_code AS code
                , lbll.asset_number AS number
                , lbll.asset_category AS category
                , lbll.asset_id AS transaction_id
                , lbll.purchase_date AS purchase_date
                , lbll.division AS division
                , lbll.qr_code_base64 as qr_code_base64
                , COALESCE(wjc.id, 0) AS cetakan_id
                , COALESCE(wjc.print_counter, 0) + 1 AS cetakan_ke 
            FROM tw_barcode_label_asset lbl
            LEFT JOIN tw_barcode_label_asset_line lbll ON lbll.label_id = lbl.id
            LEFT JOIN tw_print_counter wjc ON lbll.asset_id = wjc.transaction_id
                AND wjc.report_id = %d
                AND wjc.model_id = %d
            WHERE 1 = 1 AND lbll.id in (%s)
        """ % (report_id, model_id, ','.join([str(lbl) for lbl in label_ids]))

        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()
        
        asset_update = []
        jc_create = []
        jc_update = []
        # multidimension variable
        data = []
        col = []
        row = []
        
        for res in results:
            if res["cetakan_ke"] == 1:
                jc_create.append("""(
                    %(report_id)d, %(model_id)d, %(transaction_id)d, %(cetakan_ke)d,
                    %(uid)d, NOW() - INTERVAL '7 hours', %(uid)d, NOW() - INTERVAL '7 hours'
                )""" % {
                    'report_id': report_id,
                    'model_id': model_id,
                    'transaction_id': res["transaction_id"],
                    'cetakan_ke': res["cetakan_ke"],
                    'uid': self._uid
                })
            else:
                jc_update.append("""
                    UPDATE tw_print_counter
                    SET print_counter = %(cetakan_ke)d,
                        write_uid = %(uid)d,
                        write_date = NOW() - INTERVAL '7 hours'
                    WHERE id = %(cetakan_id)d
                """ % {
                    'cetakan_ke': res["cetakan_ke"],
                    'uid': self._uid,
                    'cetakan_id': res["cetakan_id"]
                })

            asset_update.append(int(res.get('transaction_id', 0)))
            col.append(res)
            if len(col) == 2:
                row.append(col)
                col = []
            if len(row) == 5:
                data.append(row)
                row = []
        
        if jc_create:
            self._cr.execute("""
                INSERT INTO tw_print_counter (
                    report_id, model_id, transaction_id, print_counter,
                    create_uid, create_date, write_uid, write_date
                ) VALUES %s;
            """ % ','.join(jc_create))
        
        if jc_update:
            self._cr.execute(';'.join(jc_update))

        if col:
            row.append(col)
        if row:
            data.append(row)
        
        if asset_update:
            assets = self.env['account.asset.asset'].suspend_security().browse(asset_update)
            assets.suspend_security().write({
                'is_labelled': True,
                'labelled_date': date.today(),
                'labelled_uid': self._uid
            })

        return data

    def _looping(self, data):
        return data

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.barcode.label.asset'].browse(docids)
        transaction_id = data.get('form').get('id')
       
        path = get_resource_path('tw_asset_barcode', 'static/src/images', 'logo.png')
        logo_base64 = False
        if path:
            with open(path, 'rb') as f:
                logo_base64 = base64.b64encode(f.read()).decode('ascii')

        return {
            'doc_ids': docids,
            'doc_model': 'tw.barcode.label.asset',
            'data': self._lines(data['form']),
            'docs': docs,
            'company_id': self.env.company[0],
            'user':data['user'],
            'date': fields.datetime.now().isoformat(),
            'looping': self._looping,
            'logo_base64': logo_base64
        }

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': self._lines(data['form']),
            'docs': docs,
            'company_id': docs.company_id,
            'user':data['user'],
            'date': fields.datetime.now().isoformat(),
            'looping': self._looping,
            'logo_base64': logo_base64
        }

        return self.env['report'].render('tw_asset_barcode.print_barcode_label_asset', docargs)