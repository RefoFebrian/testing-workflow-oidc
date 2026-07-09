from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class DealerSaleOrderReport(models.Model):
    _inherit = "tw.dealer.sale.order"

    power_of_attorney_type = fields.Selection([
        ('SOH', 'SOH'),
        ('Birojasa', 'Birojasa')
    ], string='Surat Kuasa', help="In the previous TEDS system, this field was called surat_kuasa_type")

    def action_print_report_dso_wizard(self):
        form_id = self.env.ref('tw_dealer_sale_order.tw_dealer_sale_order_report_wizard_view').id
        return {
            'name': 'Print Dealer Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dealer.sale.order',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'default_company_id': self.company_id.id,
            }
        }

    def action_pelunasan_leasing_bank_wizard_view(self):
        form_id = self.env.ref('tw_dealer_sale_order.tw_dealer_sale_order_pelunasan_leasing_bank_wizard_view').id
        return {
            'name': 'Pelunasan Leasing',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dealer.sale.order',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,

        }
    
    def action_surat_kuasa_wizard_view(self):
        form_id = self.env.ref('tw_dealer_sale_order.tw_dealer_sale_order_surat_kuasa_wizard_view').id
        return {
            'name': 'Surat Kuasa',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dealer.sale.order',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        }
    
    def action_print_report_dp_po(self):
        self.ensure_one()
        return self.env.ref('tw_dealer_sale_order.dp_po_dso_report').report_action(self.id)
    
    def action_print_report_pelunasan_leasing(self):
        self.ensure_one()
        return self.env.ref('tw_dealer_sale_order.pelunasan_leasing_dso_report').report_action(self.id)
    
    def action_print_report_serah_bpkb(self):
        self.ensure_one()
        return self.env.ref('tw_dealer_sale_order.serah_bpkb_dso_report').report_action(self.id)
    
    def action_print_report_invoice_dso(self):
        self.ensure_one()
        return self.env.ref('tw_dealer_sale_order.invoice_dealer_sale_order_report').report_action(self.id)
    
    def action_print_report_surat_kuasa(self):
        self.ensure_one()
        return self.env.ref('tw_dealer_sale_order.surat_kuasa_dso_report').report_action(self.id)
    
    def action_cod_settlement_wizard_view(self):
        self.ensure_one()
        return self.env.ref('tw_dealer_sale_order.cod_settlement_report').report_action(self.id)
    