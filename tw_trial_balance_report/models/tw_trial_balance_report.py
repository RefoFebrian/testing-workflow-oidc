# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwTrialBalanceReport(models.TransientModel):
    _name = "tw.trial.balance.report"
    _description = "Report Trial Balance"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()

    def _get_default_company_ids(self):
        """Get default companies from company switcher context."""
        return self.env.companies

    # 8: fields
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    status = fields.Selection([
        ('all', 'All Entries'),
        ('posted', 'Posted')
    ], string='Status', default='all')

    # 9: relation fields
    period_id = fields.Many2one('tw.account.period', string='Period')
    company_ids = fields.Many2many(
        'res.company',
        string='Branch',
        default=lambda self: self._get_default_company_ids(),
        domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)]
    )
    account_ids = fields.Many2many('account.account', string='Account')
    journal_ids = fields.Many2many('account.journal', string='Journal')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('period_id')
    def onchange_period(self):
        if self.period_id:
            self.start_date = self.period_id.date_from
            self.end_date = self.period_id.date_to

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                self.start_date = False
                self.end_date = False
                return {'warning': {'title': 'Perhatian!', 'message': 'Start Date tidak boleh melebihi End Date.'}}

    # 12: override methods

    # 13: action methods
    def action_download(self,return_fp=False):
        """Main action to generate and download report."""
        self.ensure_one()
        
        # Default to companies from company switcher if not specified
        if not self.company_ids:
            self.company_ids = self.env.companies

        # Validate that user has access to selected companies
        allowed_company_ids = self.env.user.company_ids.ids
        invalid_companies = self.company_ids.filtered(lambda c: c.id not in allowed_company_ids)
        if invalid_companies:
            raise Warning(
                f"Anda tidak memiliki akses ke company: {', '.join(invalid_companies.mapped('name'))}"
            )

        return self._print_excel_report_trial_balance(return_fp=return_fp)

    # 14: private methods
    def _get_where_clause(self):
        """Build SQL WHERE clause based on filters."""
        where_clauses = ["1=1"]

        # Get allowed company IDs for the current user
        allowed_company_ids = self.env.user.company_ids.ids

        if self.company_ids:
            # Filter to only include companies user has access to
            valid_company_ids = [c.id for c in self.company_ids if c.id in allowed_company_ids]
            if valid_company_ids:
                company_ids_str = ', '.join(str(cid) for cid in valid_company_ids)
                where_clauses.append(f"aml.company_id IN ({company_ids_str})")
            else:
                # No valid companies selected, use allowed companies
                company_ids_str = ', '.join(str(cid) for cid in allowed_company_ids)
                where_clauses.append(f"aml.company_id IN ({company_ids_str})")
        else:
            # Default to companies from company switcher context
            context_company_ids = self.env.companies.ids
            # Ensure only allowed companies are used
            valid_company_ids = [cid for cid in context_company_ids if cid in allowed_company_ids]
            if valid_company_ids:
                company_ids_str = ', '.join(str(cid) for cid in valid_company_ids)
            else:
                company_ids_str = ', '.join(str(cid) for cid in allowed_company_ids)
            where_clauses.append(f"aml.company_id IN ({company_ids_str})")

        if self.account_ids:
            account_ids_str = ', '.join(str(a.id) for a in self.account_ids)
            where_clauses.append(f"aml.account_id IN ({account_ids_str})")

        if self.journal_ids:
            journal_ids_str = ', '.join(str(j.id) for j in self.journal_ids)
            where_clauses.append(f"aml.journal_id IN ({journal_ids_str})")

        if self.status == 'posted':
            where_clauses.append("m.state = 'posted'")
        elif self.status == 'all':
            where_clauses.append("m.state IS NOT NULL")

        if self.period_id:
            where_clauses.append(f"aml.period_id = {self.period_id.id}")

        if self.start_date:
            where_clauses.append(f"aml.date >= '{self.start_date}'")

        if self.end_date:
            where_clauses.append(f"aml.date <= '{self.end_date}'")

        return " AND ".join(where_clauses)

    def _add_workbook_format(self, workbook):
        """Add workbook formats for Excel styling."""
        wbf = {}
        
        wbf['header'] = workbook.add_format({
            'bold': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFFDB', 'font_color': '#000000'
        })
        wbf['header'].set_border()

        wbf['header_no'] = workbook.add_format({
            'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000'
        })
        wbf['header_no'].set_border()
        wbf['header_no'].set_align('vcenter')

        wbf['footer'] = workbook.add_format({'align': 'left'})

        wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
        wbf['content_datetime'].set_left()
        wbf['content_datetime'].set_right()

        wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        wbf['content_date'].set_left()
        wbf['content_date'].set_right()

        wbf['title_doc'] = workbook.add_format({'bold': 1, 'align': 'left'})
        wbf['title_doc'].set_font_size(12)

        wbf['company'] = workbook.add_format({'align': 'left'})
        wbf['company'].set_font_size(11)

        wbf['content'] = workbook.add_format()
        wbf['content'].set_left()
        wbf['content'].set_right()

        wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00'})
        wbf['content_float'].set_right()
        wbf['content_float'].set_left()

        wbf['content_center'] = workbook.add_format({'align': 'center'})

        wbf['content_number'] = workbook.add_format({'align': 'right'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

        wbf['content_percent'] = workbook.add_format({'align': 'right', 'num_format': '0.00%'})
        wbf['content_percent'].set_right()
        wbf['content_percent'].set_left()

        wbf['total_float'] = workbook.add_format({
            'bold': 1, 'bg_color': '#FFFFDB', 'align': 'right', 'num_format': '#,##0.00'
        })
        wbf['total_float'].set_top()
        wbf['total_float'].set_bottom()
        wbf['total_float'].set_left()
        wbf['total_float'].set_right()

        wbf['total_number'] = workbook.add_format({
            'align': 'right', 'bg_color': '#FFFFDB', 'bold': 1
        })
        wbf['total_number'].set_top()
        wbf['total_number'].set_bottom()
        wbf['total_number'].set_left()
        wbf['total_number'].set_right()

        wbf['total'] = workbook.add_format({
            'bold': 1, 'bg_color': '#FFFFDB', 'align': 'center'
        })
        wbf['total'].set_left()
        wbf['total'].set_right()
        wbf['total'].set_top()
        wbf['total'].set_bottom()

        return wbf
