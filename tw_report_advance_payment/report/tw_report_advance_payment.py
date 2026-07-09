# 1: imports of python lib
from datetime import timedelta

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwReportAdvancePayment(models.TransientModel):
    _name = "tw.report.advance.payment"
    _description = "Report Advance Payment"

    # 7: defaults methods

    # 8: fields
    options = fields.Selection([('Advanced Payment', 'Advance Payment'), ('Settlement Advance Payment', 'Settlement Advance Payment')], string='Options', required=True, default='Advanced Payment')
    status = fields.Selection([('reconciled', 'Reconciled'), ('outstanding', 'Outstanding')], string='Status', default='outstanding')
    division = fields.Selection([('Unit', 'Unit'), ('Sparepart', 'Sparepart'), ('Umum', 'Umum')], string='Division')
    start_date = fields.Date('Start Date', default=fields.Date.context_today, required=True)
    end_date = fields.Date('End Date', default=fields.Date.context_today, required=True)

    # 9: relation fields
    company_ids = fields.Many2many('res.company', string='Branch')
    partner_ids = fields.Many2many('res.partner', string='Employee', domain=[('employee_ids', '!=', False)])
    journal_ids = fields.Many2many('account.journal', string='Journal')
    account_ids = fields.Many2many('account.account', string='Account', domain=[('account_type', '=', 'asset_receivable')])

    # 10: constraints & sql constraints
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise UserError(_('End Date harus lebih besar dari Start Date.'))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def _get_where_clause(self):
        query_where = " 1=1 "


        if self.company_ids:
            query_where += f" AND aml.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND aml.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.partner_ids:
            ids = tuple(self.partner_ids.ids)
            query_where += f" AND aml.partner_id IN {ids if len(ids) > 1 else '(%s)' % ids[0]}"

        if self.journal_ids:
            ids = tuple(self.journal_ids.ids)
            query_where += f" AND aml.journal_id IN {ids if len(ids) > 1 else '(%s)' % ids[0]}"

        if self.account_ids:
            ids = tuple(self.account_ids.ids)
            query_where += f" AND aml.account_id IN {ids if len(ids) > 1 else '(%s)' % ids[0]}"

        if self.division:
            query_where += f" AND aml.division = '{self.division}'"

        if self.start_date:
            query_where += f" AND aml.date >= '{self.start_date}'"
        if self.end_date:
            query_where += f" AND aml.date <= '{self.end_date}'"

        if self.status == 'reconciled':
            query_where += " AND aml.full_reconcile_id IS NOT NULL "
        elif self.status == 'outstanding':
            query_where += " AND aml.full_reconcile_id IS NULL "
        
        if self.options == 'Advanced Payment':
            query_where += " AND ap.move_id IS NOT NULL "
            query_where += " AND aml.debit > 0"
        else:
            query_where += " AND st.move_id IS NOT NULL "
            query_where += " AND aml.credit > 0"

        return query_where

    def action_print_report(self):
        self.ensure_one()

        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        where_clause = self._get_where_clause()
        
        query = f"""
            SELECT 
                branch.code as "Cabang",
                account.code_store->>'1' as "No Rek",
                aml.date as "Tanggal",
                move.name as "No Bukti",
                CASE WHEN aml.full_reconcile_id IS NOT NULL THEN 'Reconciled' ELSE 'Outstanding' END as "Status",
                CASE 
                    WHEN ap.id IS NOT NULL THEN ap.description 
                    ELSE COALESCE(st.description, st.name) 
                END as "Keterangan",
                COALESCE(rpb.acc_holder_name, rpb_partner.name, partner.name) as "Diberikan Ke",
                CASE 
                    WHEN ap.id IS NOT NULL THEN aml.debit 
                    ELSE aml.credit 
                END as "Total",
                st.amount_total as "Total Untaxed", 
                st.amount_gap as "Total Kembalian/Tambahan",
                creator.name as "Pembuat",
                COALESCE(ap.due_date, ap_settlement.due_date) as "Tanggal Jatuh Tempo"
            FROM account_move_line aml
            INNER JOIN account_account account ON account.id = aml.account_id
            LEFT JOIN res_company branch ON branch.id = aml.company_id
            LEFT JOIN tw_advance_payment ap ON ap.move_id = aml.move_id
            LEFT JOIN tw_settlement st ON st.move_id = aml.move_id
            LEFT JOIN tw_advance_payment ap_settlement ON ap_settlement.id = st.advance_payment_id
            LEFT JOIN res_users usr ON usr.id = aml.create_uid
            LEFT JOIN res_partner partner ON partner.id = aml.partner_id
            LEFT JOIN res_partner_bank rpb ON rpb.id = COALESCE(ap.partner_bank_id, ap_settlement.partner_bank_id)
            LEFT JOIN res_partner rpb_partner ON rpb_partner.id = rpb.partner_id
            LEFT JOIN res_partner creator ON creator.id = usr.partner_id
            LEFT JOIN account_move move ON move.id = aml.move_id
            LEFT JOIN account_journal journal ON journal.id = aml.journal_id
            WHERE {where_clause}
            ORDER BY "Tanggal", "Cabang"
        """

        self.env.cr.execute(query)
        data = self.env.cr.dictfetchall()

        if not data:
            raise UserError(_('Tidak ditemukan data untuk kriteria yang dipilih.'))

        if self.options == 'Advanced Payment':
            for row in data:
                row.pop("Total Untaxed", None)
                row.pop("Total Kembalian/Tambahan", None)

        report_name = 'Laporan Advance Payment'
        if self.options == 'Settlement Advance Payment':
            report_name = 'Laporan Settlement Advance Payment'

        return self.env['web.report'].generate_report(report_name=report_name, data=data, start_date=self.start_date, end_date=self.end_date, show_total_footer=True)
