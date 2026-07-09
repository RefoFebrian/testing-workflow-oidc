# -*- coding: utf-8 -*-

# 1: imports of python lib
import ast

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports
import logging

# 6: Import of unknown third party lib


class DealerSaleOrderInherit(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods
    
    # 8: fields
    error_message = fields.Text(string='Error Message', readonly=True)
    incentive_state = fields.Selection(
        string='Incentive State',
        selection=[('draft', 'Draft'), ('done', 'Done'), ('skip', 'Skip'), ('error', 'Error')],
        default='draft')
    incentive_retry_count = fields.Integer(string='Incentive Retry Count', default=0)
    
    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_confirm(self):
        confirm = super().action_confirm()
        
        # Direct calculate incentive on confirm, if branch setting is_calculate_incentive_on_confirm is True
        if self.company_id.branch_setting_id.is_calculate_incentive_on_confirm:
            additional_search_param = [('id', 'in', self.ids)]
            self.env['tw.employee.incentive'].sudo().check_incentive(additional_search_param=additional_search_param,raise_warning=True)

        # Cek master margin
        # self.check_master_margin()
        
        return confirm
    
    # 14: private methods
    def check_master_margin(self):
        for order in self:
            series_ids = order.order_line.mapped('product_id.series_id').ids
            
            jobs_required = {'sales', 'sc', 'sco'}

            margin_master = self.env['tw.master.target.margin'].suspend_security().search([
                ('company_id', '=', order.company_id.id),
                ('target_margin_line_ids.series_id', 'in', series_ids),
                ('state', '=', 'active')
            ])
            if not margin_master:
                raise Warning(_(
                    "Perhatian!\n"
                    f"Master target margin tidak ditemukan untuk company '{order.company_id.name}'.\n"
                    f"Untuk product '{order.order_line.product_id.name}'. "
                    "Tolong pastikan ada konfigurasi master target margin untuk kombinasi ini."
                ))

            existing_jobs = set(margin_master.mapped('job'))
            missing_job = jobs_required - existing_jobs

            if missing_job:
                raise Warning(
                    "Perhatian!\n"
                    f"Konfigurasi job belum lengkap pada master target margin untuk company '{order.company_id.name}' dan untuk produk '{order.order_line.product_id.name}'.\n"
                    f"Job yang diperlukan: {', '.join(missing_job)}.\n"
                    "Tolong pastikan ada konfigurasi master target margin untuk semua job ini."
                )

        return True
