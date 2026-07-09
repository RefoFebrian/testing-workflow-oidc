# 1: imports of python lib
from datetime import timedelta

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields
from odoo.exceptions import UserError as Warning

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwReportBankTransfer(models.TransientModel):
    _name = "tw.report.bank.transfer"
    _description = "Report Bank Transfer"

    # 7: defaults methods

    # 8: fields
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    # 9: relation fields
    company_ids = fields.Many2many('res.company', string='Branch')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def _get_where_clause(self):
        query_where = "WHERE 1=1"

        # Date filter
        if self.start_date:
            query_where += f" AND bank_transfer.date >= '{self.start_date}'"
        if self.end_date:
            query_where += f" AND bank_transfer.date <= '{self.end_date}'"

        # Company filter
        if self.company_ids:
            query_where += f" AND bank_transfer.company_id IN ({', '.join(str(i) for i in self.company_ids.ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND bank_transfer.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        return query_where

    def action_print_report(self):
        self.ensure_one()

        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = self._get_where_clause()

        query = f"""
            SELECT 
                branch_sender.code AS "Branch Code",
                branch_sender.name AS "Branch Name",
                bank_transfer.division AS "Division",
                bank_transfer.name AS "Transaction Name",
                bank_transfer.date AS "Date",
                bank_transfer.state AS "State",
                journal_sender.name->>branch_sender_partner.lang AS "Payment Method",
                COALESCE(account_sender.code_store->>CAST(branch_sender.id AS VARCHAR), '') AS "Account Code",
                account_sender.name->>branch_sender_partner.lang AS "Account Name",
                bank_transfer.amount AS "Amount",
                COALESCE(bank_transfer.bank_fee, 0) AS "Bank Transfer Fee",
                bank_transfer.description AS "Description",
                reimbursement.name AS "Reimbursed No",
                branch_destination.code AS "Branch Destination Code",
                branch_destination.name AS "Branch Destination Name",
                journal_destination.name->>branch_sender_partner.lang AS "Payment Method ",
                COALESCE(account_destination.code_store->>CAST(branch_destination.id AS VARCHAR), '') AS "Account Code ",
                account_destination.name->>branch_sender_partner.lang AS "Account Name ",
                bank_transfer_line.amount AS "Amount ",
                bank_transfer_line.description AS "Description "
            FROM tw_bank_transfer bank_transfer
            INNER JOIN tw_bank_transfer_line bank_transfer_line ON bank_transfer.id = bank_transfer_line.bank_transfer_id
            LEFT JOIN tw_reimbursement_petty_cash reimbursement ON bank_transfer_line.reimbursement_id = reimbursement.id
            LEFT JOIN res_company branch_sender ON bank_transfer.company_id = branch_sender.id
            LEFT JOIN res_partner branch_sender_partner ON branch_sender_partner.id = branch_sender.partner_id
            LEFT JOIN res_company branch_destination ON bank_transfer_line.branch_destination_id = branch_destination.id
            LEFT JOIN account_journal journal_sender ON bank_transfer.journal_id = journal_sender.id
            LEFT JOIN account_journal journal_destination ON bank_transfer_line.payment_to_id = journal_destination.id
            LEFT JOIN account_account account_sender ON journal_sender.default_credit_account_id = account_sender.id
            LEFT JOIN account_account account_destination ON journal_destination.default_debit_account_id = account_destination.id
            {query_where}
            ORDER BY bank_transfer.state, bank_transfer.date
        """

        self.env.cr.execute(query)
        data = self.env.cr.dictfetchall()

        return self.env['web.report'].generate_report(
            report_name='Laporan Bank Transfer',
            data=data,
            start_date=self.start_date,
            end_date=self.end_date,
            show_total_footer=True,
            data_summary_header={
                'B4:M4': 'Sender',
                'N4:U4': 'Recipient',
            },
            data_summary_style='header'
        )
