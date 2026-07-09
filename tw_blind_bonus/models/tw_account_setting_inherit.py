from odoo import models, fields


class BlindBonusAccountSetting(models.Model):
    _inherit = "tw.account.setting"
    _description = "Account Setting"

    journal_sale_blind_bonus_id = fields.Many2one('account.journal', string='Journal Blind Bonus Unit Sales', help='Sales Invoice Creation Journal Blind Bonus Unit')
    journal_purchase_blind_bonus_id = fields.Many2one('account.journal', string='Journal Blind Bonus Unit Purchase', help='Purchase Invoice Creation Journal Blind Bonus Unit')
    account_purchase_blind_bonus_dr_id = fields.Many2one('account.account', string='Account Blind Bonus Unit Purchase Dr', help='Account blind bonus beli unit (Dr)')
    account_purchase_blind_bonus_cr_id = fields.Many2one('account.account', string='Account Blind Bonus Unit Purchase Cr', help='Account blind bonus beli unit (Cr)')
    account_purchase_blind_bonus_performance_dr_id = fields.Many2one('account.account', string='Account Blind Bonus Unit Purchase Performance Dr', help='Account blind bonus beli unit performance (Dr)')
    account_purchase_blind_bonus_performance_cr_id = fields.Many2one('account.account', string='Account Blind Bonus Unit Purchase Performance Cr', help='Account blind bonus beli unit performance (Cr)')
    