# 1: imports of python lib
from datetime import timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

class TwReportAllPettyCash(models.TransientModel):
    _name = "tw.report.all.pettycash"
    _description = "TW Report All Petty Cash"

    # 7: defaults methods

    # 8: fields
    start_date = fields.Date('Start Date', required=True, default=fields.Date.context_today)
    end_date = fields.Date('End Date', required=True, default=fields.Date.context_today)
    option = fields.Selection([('pettycash_out', 'Petty Cash Out'), ('pettycash_in', 'Petty Cash In'), ('reimbursed', 'Reimbursed Petty Cash'), ('bank_transfer', 'Bank Transfer'),], string='Option', required=True)
    division = fields.Selection([('Unit', 'Unit'), ('Sparepart', 'Sparepart'), ('Umum', 'Umum')], string='Division')
    state_pettycash_out = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting For Approval'), ('approved', 'Approved'), ('posted', 'Posted'), ('reimbursed', 'Reimbursed'), ], string='State PCO')
    state_pettycash_in = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancelled'), ], string='State PCI')
    state_reimburse = fields.Selection([('draft', 'Draft'), ('request', 'Requested'), ('approved', 'Approved'), ('reject', 'Rejected'), ('paid', 'Paid'), ('cancel', 'Cancelled'), ], string='State RPC')
    state_bank_transfer = fields.Selection([('draft', 'Draft'), ('waiting_for_approval','Waiting For Approval'), ('approved', 'Approved'), ('posted','Posted'), ], string='State BT')

    # 9: relation fields
    journal_id = fields.Many2one('account.journal', string='Payment Method', domain="[('type', '=', 'petty_cash')]")
    journal_bt_id = fields.Many2one('account.journal', string='Bank', domain="[('type', 'in', ('bank', 'cash'))]")
    pettycash_id = fields.Many2one('tw.petty.cash.out', string='Petty Cash')
    company_ids = fields.Many2many('res.company', string='Branch')

    # 10: constraints & sql constraints
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise UserError(_('End Date harus lebih besar dari Start Date.'))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def excel_report(self):
        self.ensure_one()

        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        data_sheet = {}
        report_name = ''

        if self.option == 'pettycash_out':
            data_sheet = self._get_pettycash_out_data()
            report_name = 'Laporan Petty Cash Out'
        elif self.option == 'pettycash_in':
            data_sheet = self._get_pettycash_in_data()
            report_name = 'Laporan Petty Cash In'
        elif self.option == 'reimbursed':
            data_sheet = self._get_reimbursed_data()
            report_name = 'Laporan Reimbursed Petty Cash'
        elif self.option == 'bank_transfer':
            data_sheet = self._get_bank_transfer_data()
            report_name = 'Laporan Bank Transfer'

        data_sheet = {k: v for k, v in data_sheet.items() if v}

        if not data_sheet:
            raise UserError(_('Data tidak ditemukan.'))

        return self.env['web.report'].generate_report(report_name=report_name, data=data_sheet, data_sheet=data_sheet, start_date=self.start_date, end_date=self.end_date, show_total_footer=True)

    # 14: private methods
    def _get_where_clause(self):
        query_where = " WHERE 1=1 "

        if self.company_ids:
            if len(self.company_ids) > 1:
                query_where += " AND b.id IN %s" % str(tuple(self.company_ids.ids))
            else:
                query_where += " AND b.id = %s" % self.company_ids.id
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND b.id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.start_date:
            query_where += " AND main.date >= '%s'" % self.start_date

        if self.end_date:
            query_where += " AND main.date <= '%s'" % self.end_date

        if self.division:
            query_where += " AND main.division = '%s'" % self.division

        return query_where

    def _get_pettycash_out_data(self):
        query_where = self._get_where_clause()

        if self.state_pettycash_out:
            query_where += " AND main.state = '%s'" % self.state_pettycash_out
        else:
            query_where += " AND main.state IN ('draft', 'waiting_for_approval', 'approved', 'posted', 'reimbursed')"

        if self.journal_id:
            query_where += " AND main.journal_petty_id = %s" % self.journal_id.id

        # Summary Query
        query_summary = f"""
            SELECT 
                main.name as petty_cash_ref,
                b.code as branch_code,
                COALESCE(main.amount, 0) as total_amount,
                COALESCE(main.amount_real, 0) as total_amount_real
            FROM tw_petty_cash_out main
            LEFT JOIN res_company b ON b.id = main.company_id
            {query_where}
            ORDER BY b.code, main.date
        """

        # Details Query
        query_detail = f"""
            SELECT 
                main.name as petty_cash_ref,
                b.code as branch_code,
                bd.code as branch_destination,
                main.division as division,
                main.date as date,
                j.name->>bp.lang as journal,
                e.name as responsible,
                l.name as description,
                CASE 
                    WHEN main.state = 'draft' THEN 'Draft'
                    WHEN main.state = 'confirmed' THEN 'Confirmed'
                    WHEN main.state = 'waiting_for_approval' THEN 'Waiting For Approval'
                    WHEN main.state = 'approved' THEN 'Approved'
                    WHEN main.state = 'posted' THEN 'Posted'
                    WHEN main.state = 'reimbursed' THEN 'Reimbursed'
                    WHEN main.state = 'cancel' THEN 'Cancelled'
                    ELSE main.state
                END as state,
                COALESCE(l.amount, 0) as total_amount,
                COALESCE(l.amount_real, 0) as total_amount_real
            FROM tw_petty_cash_out main
            JOIN tw_petty_cash_out_line l ON l.petty_cash_out_id = main.id
            LEFT JOIN res_company b ON b.id = main.company_id
            LEFT JOIN res_partner bp ON bp.id = b.partner_id
            LEFT JOIN res_company bd ON bd.id = main.branch_destination_id
            LEFT JOIN account_journal j ON j.id = main.journal_petty_id
            LEFT JOIN hr_employee e ON e.id = main.employee_id
            {query_where}
            ORDER BY b.code, main.date
        """

        self.env.cr.execute(query_summary)
        summary_data = self.env.cr.dictfetchall()

        self.env.cr.execute(query_detail)
        detail_data = self.env.cr.dictfetchall()

        return {
            'Laporan Petty Cash Out': summary_data,
            'Laporan Petty Cash Out Details': detail_data
        }

    def _get_pettycash_in_data(self):
        query_where = self._get_where_clause()

        if self.state_pettycash_in:
            query_where += " AND main.state = '%s'" % self.state_pettycash_in
        else:
            query_where += " AND main.state IN ('draft', 'posted', 'cancel')"

        if self.journal_id:
            query_where += " AND main.journal_id = %s" % self.journal_id.id

        if self.pettycash_id:
            query_where += " AND main.petty_cash_out_id = %s" % self.pettycash_id.id

        # Summary
        query_summary = f"""
            SELECT 
                main.name as petty_cash_in_ref,
                b.code as branch_code,
                pco.name as petty_cash_out_ref,
                COALESCE(main.amount, 0) as total_amount
            FROM tw_petty_cash_in main
            LEFT JOIN tw_petty_cash_out pco ON pco.id = main.petty_cash_out_id
            LEFT JOIN res_company b ON b.id = main.company_id
            {query_where}
            ORDER BY b.code, main.date
        """

        # Details
        query_detail = f"""
            SELECT 
                main.name as petty_cash_in_ref,
                b.code as branch_code,
                bd.code as branch_destination,
                pco.name as petty_cash_out_ref,
                main.division as division,
                main.date as date,
                j.name->>bp.lang as journal,
                l.name as description,
                CASE 
                    WHEN main.state = 'draft' THEN 'Draft'
                    WHEN main.state = 'confirmed' THEN 'Confirmed'
                    WHEN main.state = 'waiting_for_approval' THEN 'Waiting For Approval'
                    WHEN main.state = 'approved' THEN 'Approved'
                    WHEN main.state = 'posted' THEN 'Posted'
                    WHEN main.state = 'cancel' THEN 'Cancelled'
                    ELSE main.state
                END as state,
                COALESCE(l.amount, 0) as total_amount
            FROM tw_petty_cash_in main
            JOIN tw_petty_cash_in_line l ON l.petty_cash_in_id = main.id
            LEFT JOIN tw_petty_cash_out pco ON pco.id = main.petty_cash_out_id
            LEFT JOIN res_company b ON b.id = main.company_id
            LEFT JOIN res_partner bp ON bp.id = b.partner_id
            LEFT JOIN res_company bd ON bd.id = main.branch_destination_id
            LEFT JOIN account_journal j ON j.id = main.journal_id
            {query_where}
            ORDER BY b.code, main.date
        """

        self.env.cr.execute(query_summary)
        summary_data = self.env.cr.dictfetchall()

        self.env.cr.execute(query_detail)
        detail_data = self.env.cr.dictfetchall()

        return {
            'Laporan Petty Cash In': summary_data,
            'Laporan Petty Cash In Details': detail_data
        }

    def _get_reimbursed_data(self):
        query_where = self._get_where_clause()

        if self.state_reimburse:
            query_where += " AND main.state = '%s'" % self.state_reimburse
        else:
            query_where += " AND main.state IN ('draft', 'request', 'approved', 'reject', 'paid', 'cancel')"

        if self.journal_id:
            query_where += " AND main.journal_id = %s" % self.journal_id.id

        # Summary
        query_summary = f"""
            SELECT 
                main.name as reimburse_ref,
                b.code as branch_code,
                COALESCE(main.amount_total, 0) as total_amount_real
            FROM tw_reimbursement_petty_cash main
            LEFT JOIN res_company b ON b.id = main.company_id
            {query_where}
            ORDER BY b.code, main.date
        """

        query_detail = f"""
            SELECT 
                main.name as reimburse_ref,
                b.code as branch_code,
                main.division as division,
                main.date as date_request,
                main.confirm_date as date_approve,
                main.cancel_date as date_cancel,
                l.name as petty_cash_out_ref,
                l.date as petty_cash_out_date,
                bd.code as branch_destination,
                CASE 
                    WHEN main.state = 'draft' THEN 'Draft'
                    WHEN main.state = 'confirmed' THEN 'Confirmed'
                    WHEN main.state = 'waiting_for_approval' THEN 'Waiting For Approval'
                    WHEN main.state = 'approved' THEN 'Approved'
                    WHEN main.state = 'paid' THEN 'Paid'
                    WHEN main.state = 'cancel' THEN 'Cancelled'
                    ELSE main.state
                END as state,
                COALESCE(l.amount_real, 0) as total_amount_real
            FROM tw_reimbursement_petty_cash main
            JOIN tw_petty_cash_out l ON l.reimbursed_id = main.id
            LEFT JOIN res_company b ON b.id = main.company_id
            LEFT JOIN res_company bd ON bd.id = l.branch_destination_id
            {query_where}
            ORDER BY b.code, main.date
        """

        self.env.cr.execute(query_summary)
        summary_data = self.env.cr.dictfetchall()

        self.env.cr.execute(query_detail)
        detail_data = self.env.cr.dictfetchall()

        return {
            'Laporan Reimburse': summary_data,
            'Laporan Reimburse Details': detail_data
        }

    def _get_bank_transfer_data(self):
        query_where = self._get_where_clause()

        if self.state_bank_transfer:
            query_where += " AND main.state = '%s'" % self.state_bank_transfer
        else:
            query_where += " AND main.state IN ('draft', 'waiting_for_approval', 'approved', 'posted')"

        if self.journal_bt_id:
            query_where += " AND main.journal_id = %s" % self.journal_bt_id.id

        # Summary
        query_summary = f"""
            SELECT 
                main.name as bank_transfer_ref,
                b.code as branch_code,
                COALESCE(main.amount_total, 0) as total_amount
            FROM tw_bank_transfer main
            LEFT JOIN res_company b ON b.id = main.company_id
            {query_where}
            ORDER BY b.code, main.date
        """

        # Details
        query_detail = f"""
            SELECT 
                main.name as bank_transfer_ref,
                b.code as branch_code,
                main.division as division,
                main.date as date,
                r.name as reimburse_ref,
                l.description as description,
                bd.code as branch_dest,
                CASE 
                    WHEN main.state = 'draft' THEN 'Draft'
                    WHEN main.state = 'waiting_for_approval' THEN 'Waiting For Approval'
                    WHEN main.state = 'approved' THEN 'Approved'
                    WHEN main.state = 'posted' THEN 'Posted'
                    WHEN main.state = 'done' THEN 'Done'
                    WHEN main.state = 'reject' THEN 'Rejected'
                    WHEN main.state = 'cancel' THEN 'Cancelled'
                    ELSE main.state
                END as state,
                COALESCE(l.amount, 0) as total_amount
            FROM tw_bank_transfer main
            JOIN tw_bank_transfer_line l ON l.bank_transfer_id = main.id
            LEFT JOIN res_company b ON b.id = main.company_id
            LEFT JOIN res_company bd ON bd.id = l.branch_destination_id
            LEFT JOIN tw_reimbursement_petty_cash r ON r.id = l.reimbursement_id
            {query_where}
            ORDER BY b.code, main.date
        """

        self.env.cr.execute(query_summary)
        summary_data = self.env.cr.dictfetchall()

        self.env.cr.execute(query_detail)
        detail_data = self.env.cr.dictfetchall()

        return {
            'Laporan Bank Transfer': summary_data,
            'Laporan Bank Transfer Details': detail_data
        }
