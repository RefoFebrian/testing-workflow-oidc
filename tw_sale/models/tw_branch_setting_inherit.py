from odoo import models, fields


class SaleAccountSetting(models.Model):
    _inherit = "tw.account.setting"
    _description = "Account Setting - Sales"
   
    journal_sales_unit_id = fields.Many2one(
        'account.journal', 
        string='Journal Unit Sales', 
        help='Sales Invoice Creation Journal Unit',
        domain="[('type', '=', 'sale')]"
    )
    journal_sales_sparepart_id = fields.Many2one(
        'account.journal', 
        string='Journal Sparepart Sales', 
        help='Sales Invoice Creation Journal Sparepart',
        domain="[('type', '=', 'sale')]"
    )
    