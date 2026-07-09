# 1: imports of python lib
from datetime import timedelta

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwReportPayment(models.TransientModel):
    _name = "tw.report.payment"
    _description = "Report Payment"

    # 7: defaults methods

    # 8: fields
    start_date = fields.Date('Start Date', default=fields.Date.context_today)
    end_date = fields.Date('End Date', default=fields.Date.context_today)
    division = fields.Selection([('Unit', 'Unit'), ('Sparepart', 'Sparepart'), ('Umum', 'Umum')], string='Division')
    option = fields.Selection([('customer_payment_detail', 'Customer Payment'), ('supplier_payment_detail', 'Supplier Payment'), ('receive_payment_detail', 'Receive Payment')], string='Option', required=True)

    # 9: relation fields
    company_ids = fields.Many2many('res.company', string='Branch')
    account_ids = fields.Many2many('account.account', string='Account')
    journal_ids = fields.Many2many('account.journal', string='Journal')
    partner_ids = fields.Many2many('res.partner', string='Partner')

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
        query_where = "WHERE 1=1 and av.state = 'paid'"

        # Date Filter
        if self.start_date:
            query_where += f" AND av.date >= '{self.start_date}'"
        if self.end_date:
            query_where += f" AND av.date <= '{self.end_date}'"

        # Division Filter
        if self.division:
            query_where += f" AND av.division = '{self.division}'"

        # Map option to DB type
        option_map = {'customer_payment_detail': 'customer_payment', 'supplier_payment_detail': 'supplier_payment', 'receive_payment_detail': 'receive_payment',}
        query_where += f" AND av.type = '{option_map[self.option]}'"

        # Filter Many2many
        if self.company_ids:
            query_where += f" AND av.company_id IN ({', '.join(str(i) for i in self.company_ids.ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND av.company_id IN {str(tuple(branch)).replace(',)', ')')}"
        if self.account_ids:
            query_where += f" AND av.account_id IN ({', '.join(str(i) for i in self.account_ids.ids)})"
        if self.journal_ids:
            query_where += f" AND av.journal_id IN ({', '.join(str(i) for i in self.journal_ids.ids)})"
        if self.partner_ids:
            query_where += f" AND av.partner_id IN ({', '.join(str(i) for i in self.partner_ids.ids)})"

        return query_where

    def action_print_report(self):
        self.ensure_one()

        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = self._get_where_clause()

        # Sheet 1
        query_sheet1 = f"""
            SELECT 
                c.code as "Partner",
                av.name as "Partner_Reference",
                SUM(CASE WHEN avl.type='cr' THEN avl.amount ELSE 0 END) as "Credit",
                SUM(CASE WHEN avl.type='dr' THEN avl.amount ELSE 0 END) as "Debit",
                SUM(CASE WHEN avl.type='cr' THEN avl.amount ELSE 0 END) - SUM(CASE WHEN avl.type='dr' THEN avl.amount ELSE 0 END) as "Balance",
                av.confirm_date as "Tanggal_Approval",
                COALESCE(he.name, confirm_partner.name) as "Employee",
                g.name->>branch_partner.lang as "Jabatan", 
                tal.limit as "Limit"
            FROM tw_account_payment av 
            LEFT JOIN res_company branch ON branch.id = av.company_id
            LEFT JOIN res_partner branch_partner ON branch_partner.id = branch.partner_id
            LEFT JOIN tw_account_payment_line avl ON avl.payment_id = av.id
            LEFT JOIN res_company c ON av.company_id = c.id 
            LEFT JOIN res_partner p ON av.partner_id = p.id
            LEFT JOIN res_users confirm_user ON av.confirm_uid = confirm_user.id
            LEFT JOIN res_partner confirm_partner ON confirm_user.partner_id = confirm_partner.id
            LEFT JOIN LATERAL (
                SELECT transaction_id, MAX("limit") as max_limit
                FROM tw_approval_line
                WHERE transaction_id = av.id
                and model_id = (SELECT id FROM ir_model WHERE model = 'tw.account.payment' LIMIT 1)
                AND state = 'approve'
                GROUP BY transaction_id
            ) max_app ON max_app.transaction_id = av.id
            left join LATERAL(
            	select al.*
            	from tw_approval_line al 
            	WHERE al.transaction_id = av.id
                AND al.limit = max_app.max_limit
                AND al.model_id = (SELECT id FROM ir_model WHERE model = 'tw.account.payment' LIMIT 1)
                AND al.state = 'approve'
                order by id desc
                limit 1
            ) as tal on tal.transaction_id = av.id
            LEFT JOIN res_groups g ON tal.group_id = g.id
            LEFT JOIN res_users approver_user ON tal.approver_id = approver_user.id
            LEFT JOIN hr_employee he ON he.user_id = approver_user.id
            {query_where}
            GROUP BY av.id, c.code, p.name, confirm_partner.name, he.name, g.name, tal.limit, branch_partner.id
            ORDER BY av.name ASC
        """

        # Sheet 2
        query_sheet2 = f"""
            SELECT 
                c.code as "Cabang",
                c.name as "Nama_Cabang",
                c_to.code as "Terima_Untuk",
                c_to.name as "Cabang_Untuk",
                av.name as "Number",
                av.state as "Status",
                j.name->>branch_partner.lang as "Payment_Method",
                COALESCE((aa.code_store->>'1') || (c.code), (aa_j.code_store->>'1') || (c.code)) as "Account",
                av.amount as "Paid_Amount",
                COALESCE(p.code, p.ref, p.name) as "Partner",
                p.name as "Nama_Partner",
                COALESCE(aml.ref, av.name) as "No_Transaksi",
                (CASE WHEN avl.type='dr' THEN avl.amount ELSE 0 END) AS "Debit",
                (CASE WHEN avl.type='cr' THEN avl.amount ELSE 0 END) AS "Credit",
                av.writeoff_amount as "Diff",
                create_partner.name as "Create_By",
                av.create_date as "Create_On"
            FROM tw_account_payment av
            INNER JOIN tw_account_payment_line avl ON avl.payment_id = av.id
            LEFT JOIN account_move_line aml ON avl.move_line_id = aml.id
            LEFT JOIN res_company c ON av.company_id = c.id
            LEFT JOIN res_company c_to ON av.beneficiary_company_id = c_to.id
            LEFT JOIN res_partner branch_partner ON branch_partner.id = c.partner_id
            LEFT JOIN account_journal j ON av.journal_id = j.id
            LEFT JOIN account_account aa ON aml.account_id = aa.id
            LEFT JOIN account_account aa_j ON avl.account_id = aa_j.id
            LEFT JOIN res_partner p ON av.partner_id = p.id
            LEFT JOIN res_users create_user ON av.create_uid = create_user.id
            LEFT JOIN res_partner create_partner ON create_user.partner_id = create_partner.id
            {query_where}
            ORDER BY av.name ASC
        """

        # Execute Sheet 1
        self._cr.execute(query_sheet1)
        summary_data = self._cr.dictfetchall()

        # Execute Sheet 2
        self._cr.execute(query_sheet2)
        detail_data = self._cr.dictfetchall()

        if not summary_data and not detail_data:
            raise UserError(_('Tidak ditemukan data untuk kriteria yang dipilih.'))

        report_name = {'customer_payment_detail': 'Laporan Customer Payment', 'supplier_payment_detail': 'Laporan Supplier Payment', 'receive_payment_detail': 'Laporan Receive Payment', }.get(self.option, 'Laporan Payment')

        data_sheet = {report_name: summary_data or [{'Info': 'No Data'}], f"{report_name} Details": detail_data or [{'Info': 'No Data'}], }
        return self.env['web.report'].generate_report(report_name=report_name, data=summary_data or detail_data, data_sheet=data_sheet, start_date=self.start_date, end_date=self.end_date)
    