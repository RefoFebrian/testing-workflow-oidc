# 1: imports of python lib
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class BankReconcileMutasiReport(models.TransientModel):
    _name = "tw.bank.reconcile.mutasi.report"
    _description = 'Laporan Mutasi Bank Reconcile'

    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return [company_ids[0].id]
        return []
    
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    wbf = {}

    # 8: fields
    name = fields.Char('Filename', readonly=True)
    state_x = fields.Selection((
        ('choose', 'choose'),
        ('get', 'get')
    ), default=lambda *a: 'choose')
    state = fields.Selection([
        ('all', 'All'),
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('auto_reconciled', 'Auto Reconcile'),
        ('cancel', 'Cancel')
    ], string='Status', default='all')
    start_date = fields.Date(string='Start Date', default=_get_default_date)
    end_date = fields.Date(string='End Date', default=_get_default_date)
    data_x = fields.Binary(string='File', readonly=True)

    # 9: relation fields
    company_ids = fields.Many2many(comodel_name='res.company', relation='tw_bank_reconcile_mutasi_report_company_rel', column1='bank_reconcile_mutasi_report_id', column2='company_id', string='Branch', copy=False, default=_get_default_branch)
    account_bank_ids = fields.Many2many(comodel_name='account.account', relation='tw_bank_reconcile_mutasi_report_account_account_rel', column1='bank_reconcile_mutasi_report_id', column2='account_id', string='Account', domain="[('account_type','in',('asset_cash', 'asset_current')), ('company_ids','!=',False)]", copy=False)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_bank_reconcile_mutasi_report_tree(self):
        domain = []
        name = 'Laporan Mutasi Bank Reconcile'
        path = 'laporan-mutasi-bank-reconcile'
        form_view_id = self.env.ref('tw_bank_reconcile.tw_bank_reconcile_mutasi_report_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.bank.reconcile.mutasi.report',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_export(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        start_date = self.start_date
        end_date = self.end_date
        company_ids = self.company_ids
        account_bank_ids = self.account_bank_ids
        state = self.state

        query_where = ' WHERE 1=1'
        if company_ids:
            query_where += f" AND wb.id IN {str(tuple([b.id for b in company_ids])).replace(',)', ')')}"
        if account_bank_ids:
            query_where += f" AND aa.id IN {str(tuple([aa.id for aa in account_bank_ids])).replace(',)', ')')}"
        if state != 'all':
            query_where += f" AND tbr.state = '{str(state)}'"

        query = f"""
            SELECT
                tbr.name AS name
                , tbm.name AS no_bank_mutasi
                , tbm.date AS date
                , wb.name AS branch
                , COALESCE(tbm.remark, '') AS remark
                , COALESCE(tbm.no_sistem, '') AS no_sistem
                , COALESCE(aml.ref, '') AS reference
                , COALESCE(tbm.debit, 0) AS debit
                , COALESCE(tbm.credit, 0) AS credit
            FROM tw_bank_reconcile tbr
            LEFT JOIN res_company wb ON tbr.company_id = wb.id
            LEFT JOIN account_account aa ON tbr.account_id = aa.id
            LEFT JOIN tw_bank_reconcile_tw_bank_mutasi_rel bmr ON bmr.bank_reconcile_id = tbr.id
            LEFT JOIN tw_bank_mutasi tbm ON bmr.mutasi_bank_id = tbm.id
            LEFT JOIN tw_bank_reconcile_account_move_line_rel tbrr ON tbrr.bank_reconcile_id = tbr.id
            LEFT JOIN account_move_line aml ON tbrr.line_id = aml.id
            {query_where}
            AND (tbm.debit = aml.credit AND tbm.credit = aml.debit)
            AND tbr.date BETWEEN '{start_date}' AND '{end_date}'
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()

        return self.env['web.report'].sudo().generate_report('Laporan Bank Reconcile', ress, start_date=self.start_date, end_date=self.end_date)

    # 14: private methods