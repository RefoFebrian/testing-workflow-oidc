# part_hotline_report.py

from datetime import datetime
from odoo import models

class PartHotlineReport(models.AbstractModel):
    _name = "report.tw_part_hotline.tw_part_hotline_print_pdf"
    _description = "TW Part Hotline Report"

    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.part.hotline'].browse(docids)
        res = []

        for doc in docs:
            dp_ids = []
            detail = []

            for dp in doc.alocation_dp_ids:
                dp_ids.append({
                    'name': dp.hl_id.ref,
                    'amount': dp.amount_hl_allocation
                })

            for line in doc.part_detail_ids:
                detail.append({
                    'product': line.product_id.display_name,
                    'qty': line.qty,
                    'price': line.price,
                    'tax': line.tax_id.name,
                    'subtotal': line.subtotal    
                })

            dp_total = '50%'
            md_code = self.env['res.company'].get_default_main_dealer_code()
            partner_id = self.env['res.partner'].sudo().search([('code','=',md_code)], limit=1)
            if doc.company_id.default_supplier_id.id == partner_id.id:
                dp_total = '100%'

            res.append({
                'today': datetime.now(),
                'user': self.env.user.name,
                'company_id': f"[{doc.company_id.code}] {doc.company_id.name}",
                'date': doc.date,
                'no_hotline': doc.name,
                'customer': doc.customer_id.display_name,
                'mobile': doc.mobile,
                'engine_number': doc.lot_id.name,
                'dp_ids': dp_ids,
                'detail': detail,
                'amount_untaxed': doc.amount_untaxed,
                'amount_tax': doc.amount_tax,
                'amount_total': doc.amount_total,
                'dp_total': dp_total,
                'doc': doc
            })

        return {
            'doc_ids': docids,
            'doc_model': 'tw.part.hotline',
            'docs': res,
        }
