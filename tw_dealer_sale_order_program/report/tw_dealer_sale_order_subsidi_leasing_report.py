from odoo import models, fields, api, _
from . import fungsi_terbilang


class PrintSubsidiLeasingDealerSaleOrder(models.AbstractModel):
    _name = "report.tw_dealer_sale_order_discount.subsidi_leasing"
    _description = "Dealer Sale Order Report Subsidi Leasing"
    
    def time_date(self, date):
        return date.strftime("%d-%m-%Y %H:%M")
    
    def terbilang(self, amount):
        # Handle string input (e.g., "800.000,00") if passed from report
        if isinstance(amount, str):
            amount = float(amount.replace(".", "").replace(",", "."))
        return fungsi_terbilang.terbilang(amount, "idr", 'id')
    
    def get_subsidi_leasing_amount(self):
        """Return numeric float value (untuk terbilang)."""
        dso = self.env['tw.dealer.sale.order'].browse(self.env.context.get('active_ids', []))
        total_subsidi_leasing = 0
        for line in dso.order_line:
            for disc in line.sales_program_ids:
                total_subsidi_leasing += disc.amount_finco
        return float(total_subsidi_leasing)

    def get_subsidi_leasing(self):
        """Return formatted string: 800.000,00 (untuk tampilan di QWeb)."""
        amount = self.get_subsidi_leasing_amount()
        formatted = "{:,.2f}".format(amount)
        # Konversi dari format US (800,000.00) ke format ID (800.000,00)
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    def get_subsidi_leasing_formatted(self):
        """Alias untuk backward compatibility."""
        return self.get_subsidi_leasing()
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.dealer.sale.order'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'tw.dealer.sale.order',
            'docs': docs,
            'time_date': self.time_date,
            'terbilang': self.terbilang,
            'get_subsidi_leasing': self.get_subsidi_leasing,
            'get_subsidi_leasing_formatted': self.get_subsidi_leasing_formatted,
        }