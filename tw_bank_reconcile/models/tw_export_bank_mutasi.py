# 1: imports of python lib
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class ExportBankMutasi(models.TransientModel):
    _name = "tw.export.bank.mutasi"
    _description = 'Export Bank Mutasi'

    # 7: defaults methods
    def _get_default_branch(self):
        return self.env.user.company_ids[0].id if self.env.user.company_ids else False
    
    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_default_start_date(self):
        return date.today().replace(day=1)

    def _get_default_end_date(self):
        return date.today() - relativedelta(days=1)

    wbf = {}

    # 8: fields
    name = fields.Char('Filename', readonly=True)
    state_x = fields.Selection((
        ('choose', 'choose'),
        ('get', 'get')
    ), default=lambda *a: 'choose')
    options = fields.Selection([
        ('All', 'All'),
        ('No Sistem Kosong', 'No Sistem Kosong')
    ], string='Options', default='No Sistem Kosong')
    status = fields.Selection([
        ('All', 'All'),
        ('Outstanding', 'Outstanding'),
        ('Reconciled', 'Reconciled')
    ], string='Status', default='All')
    tgl_upload = fields.Date('Tanggal Upload')
    tgl_mutasi = fields.Date('Tanggal Mutasi')
    start_date = fields.Date('Start Date', default=_get_default_start_date)
    end_date = fields.Date('End Date', default=_get_default_end_date)
    data_x = fields.Binary('File', readonly=True)

    # 9: relation fields
    account_id = fields.Many2one(comodel_name='account.account', string='Account', domain="[('account_type','in',('asset_cash', 'asset_current')), ('company_ids','=',company_id)]")
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', default=_get_default_branch)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_export_bank_mutasi_tree(self):
        domain = []
        name = 'Export Bank Mutasi'
        path = 'export-bank-mutasi'
        form_view_id = self.env.ref('tw_bank_reconcile.tw_export_bank_mutasi_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.export.bank.mutasi',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_export(self):
        self.ensure_one()
        if self.options:
            return self._print_export_bank_mutasi()
        
    # 14: private methods
    def _print_export_bank_mutasi(self):
        company_id = self.company_id.id
        tgl_upload = self.tgl_upload
        tgl_mutasi = self.tgl_mutasi
        account_id = self.account_id.id
        status = self.status
        options = self.options

        query_where = ' WHERE 1=1'
        if company_id:
            query_where += f' AND bm.company_id = {company_id}'
        if tgl_upload:
            query_where += f" AND bm.date_upload = '{tgl_upload}'"
        if tgl_mutasi:
            query_where += f" AND bm.date = '{tgl_mutasi}'"
        if self.start_date:
            query_where += f" AND bm.date >= '{self.start_date}'"
        if self.end_date:
            query_where += f" AND bm.date <= '{self.end_date}'"

        if status:
            if status == 'Outstanding':
                query_where += " AND bm.state = 'Outstanding'"
            elif status == 'Reconciled':
                query_where += " AND bm.state IN ('Reconciled', 'Auto Reconcile')"
        if account_id:
            query_where += f" AND bm.account_id = {account_id}"
        if options == 'No Sistem Kosong':
            query_where += " AND (bm.no_sistem = '' OR bm.no_sistem IS NULL)"
        
        query = f"""
            SELECT
                name
                , date tanggal
                , date_upload 
                , remark
                , teller
                , debit
                , credit
                , saldo saldo_akhir
                , coa
                , no_sistem
                , state status
            FROM tw_bank_mutasi bm
            {query_where}
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        date = self._get_default_datetime()
        date = date.strftime("%d-%m-%Y %H:%M:%S")
        filename = 'Export Bank Mutasi ' + str(date) + '.xlsx'

        return self.env['web.report'].sudo().generate_report(filename, ress)