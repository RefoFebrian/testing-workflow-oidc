# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwDgiInvoiceCron(models.Model):
    _name = "tw.dgi.invoice.cron"
    _description = "Cron for sending DGI Invoice"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    @api.model
    def schedulle_send_dgi_invoice(self, limit=100):
        dso_records = self.env['tw.dealer.sale.order'].search([
            ('dgi_invoice_status', '=', 'draft')
        ], limit=limit)
        
        if dso_records:
            for dso in dso_records:
                dso.action_send_dgi_invoice_h1()
                self.env.cr.commit()

        wo_records = self.env['tw.work.order'].search([
            ('dgi_invoice_status', '=', 'draft'),
            ('is_invoiced', '=', True),
        ], limit=limit)
        
        if wo_records:
            for wo in wo_records:
                wo.action_send_dgi_invoice_h23()
                self.env.cr.commit()

    @api.model
    def schedulle_retry_dgi_invoice_error(self, limit=100):
        dso_error_records = self.env['tw.dealer.sale.order'].search([
            ('dgi_invoice_status', '=', 'error'),
            ('dgi_err_count_inv', '<', 3)
        ], limit=limit)
        if dso_error_records:
            dso_error_records.write({'dgi_invoice_status': 'draft'})

        wo_error_records = self.env['tw.work.order'].search([
            ('dgi_invoice_status', '=', 'error'),
            ('dgi_err_count_inv', '<', 3)
        ], limit=limit)
        if wo_error_records:
            wo_error_records.write({'dgi_invoice_status': 'draft'})
