from odoo import models, fields


class PartSaleAccountSetting(models.Model):
    _inherit = "tw.account.setting"
    _description = "Part Sale Account Setting"
   
    journal_part_sales_umum_id = fields.Many2one('account.journal', string='Journal Part Sales Umum', help='Part Sales Invoice Creation Journal Umum')
    journal_part_sales_sparepart_id = fields.Many2one('account.journal', string='Journal Part Sales Sparepart', help='Part Sales Invoice Creation Journal Sparepart')
    