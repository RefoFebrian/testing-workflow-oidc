from odoo import models, fields, api

class TwTrialBalanceReportInherit(models.TransientModel):
    _inherit = "tw.trial.balance.report"

    def generate_trial_balance_report(self,kwargs):
        period_id = kwargs.get('period_id')

        report = self.create({
            'period_id': period_id,
        })

        return report.action_download(return_fp=True)