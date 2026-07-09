from odoo import models, fields


class SaleBranchSetting(models.Model):
    _inherit = "tw.branch.setting"
    _description = "Branch Setting"
    
    sale_blind_bonus_amount = fields.Float(string="Sale Blind Bonus Amount")
    purchase_blind_bonus_amount = fields.Float(string="Purchase Blind Bonus Amount")
    purchase_performance_blind_bonus_amount = fields.Float(string="Purchase Performance Blind Bonus Amount")
