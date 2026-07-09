from odoo import models, fields, api


class TwBranchSettingInherit(models.Model):
    _inherit = "tw.branch.setting"

    is_calculate_incentive_on_confirm = fields.Boolean(string='Calculate Incentive on Confirm', default=True, help="If checked, the incentive will be calculated automatically when the dealer sale order is confirmed, and blocking the DSO confirmation if there is an error on incentive checking. If unchecked, the incentive will be calculated by scheduller.")
    