# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError as Warning

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderCollecting(models.Model):
    _name = "tw.work.order.collecting"
    _description = "TW Work Order Collecting"
    _order = "date desc"

    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False

    def _get_default_date(self):
        return fields.Date.today()

    # 8: fields
    name = fields.Char('Collecting', size=64, readonly=True)
    supplier_ref = fields.Char(string='No. Claim MD',size=64)
    confirm_date = fields.Datetime('Confirmed on')
    date  =  fields.Date('Date',default=_get_default_date)
    start_date  =  fields.Date(string='Start Date')
    end_date  =  fields.Date(string='End Date')
    due_date = fields.Date('Due Date')
    amount = fields.Float(string='Amount')
    transaction_message = fields.Text(string='Message',help='Menyediakan informasi banyaknya WO yg harus di Collect')
    claim_type_id = fields.Many2one(
        'tw.selection',
        string='Claim Type',
        domain="[('type', '=', 'WorkOrderClaimType')]",
    )
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(),default='Sparepart',required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted')
    ], 'State', readonly=True, default='draft')

    # 9: relation fields
    company_id = fields.Many2one('res.company','Branch',required=True, default=_get_default_branch)
    supplier_id = fields.Many2one('res.partner','Supplier',required=True)
    invoice_id = fields.Many2one('account.move','Invoice')
    confirm_uid = fields.Many2one('res.users',string="Confirmed by")
    work_order_ids = fields.One2many('tw.work.order','collecting_work_order_id')
    collecting_line_ids = fields.One2many('tw.work.order.collecting.line','collecting_work_order_id')
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('name', 'invoice_id')
    def _compute_invoice_count(self):
        for rec in self:
            domain = [('ref', '=', rec.name)]
            if rec.invoice_id:
                domain = ['|', ('id', '=', rec.invoice_id.id), ('ref', '=', rec.name)]
            rec.invoice_count = self.env['account.move'].sudo().search_count(domain)

    def action_view_invoice(self):
        self.ensure_one()
        domain = [('ref', '=', self.name)]
        if self.invoice_id:
            domain = ['|', ('id', '=', self.invoice_id.id), ('ref', '=', self.name)]
        invoices = self.env['account.move'].sudo().search(domain)
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
        if len(invoices) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.id
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
        return action

    def _prepare_onchange_branch_type_date(self):
        """Hitung due_date berdasarkan value dari claim_type_id."""
        today = self._get_default_date()
        self.due_date = today
        if self.claim_type_id and self.claim_type_id.value == 'CLA':
            self.due_date = today + relativedelta(days=60)
        return self.due_date

    @api.onchange('company_id', 'claim_type_id', 'start_date', 'end_date')
    def _onchange_branch_type_date(self):
        self.work_order_ids = False
        self.collecting_line_ids = False
        self.due_date = False
        self.amount = 0.0
        if self.claim_type_id:
            self._prepare_onchange_branch_type_date()
        
    @api.onchange('company_id')
    def branch_change(self):
        self.supplier_id=self.company_id.default_supplier_id

    # 12: override methods    
    def action_get_detail(self):
        wo = []
        self.transaction_message = False
        limit = 50
        if not self.claim_type_id:
            raise ValidationError(_('Pilih Claim Type terlebih dahulu.'))
        work_order_obj = self.env['tw.work.order'].search([
            ('company_id', '=', self.company_id.id),
            ('collecting_work_order_id', '=', False),
            ('state', 'in', ['sale', 'done']),
            ('claim_state', '=', 'draft'),
            ('claim_type_id', '=', self.claim_type_id.id),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])

        # Filter: hanya ambil WO yang invoice receivable line-nya belum ter-reconcile
        work_order_obj = self._filter_wo_unreconciled(work_order_obj)

        if work_order_obj :
            length = len(work_order_obj)
            if length > limit:
                # Sisakan transaksi sebesar "limit", delete sisanya. tidak ditaruh pada query untuk mengcapture total data
                del work_order_obj[limit:]
                transaction_remaining = length//limit or 1
                self.transaction_message = 'Anda menggenerate "%s WO dari total %s WO yang harus di proses" di transaksi ini. \nSilahkan buat setidaknya %s collecting lagi untuk menyelesaikannya. ' %(limit,length,transaction_remaining)
            for work_order in work_order_obj:
                wo.append(work_order.id)
            # Update collecting_work_order_id
            self.write({'work_order_ids': [(6,0,wo)]})
            self.get_rekap_collecting_line_ids()
        else :
            raise ValidationError(_('Data Tidak Ditemukan'))
        
    def _get_claim_journal_ids(self):
        """
        Ambil journal_id dari master tw.work.order.claim berdasarkan claim_type_id relasi langsung.
        Return list of journal ids yang digunakan untuk filtering invoice WO.
        """
        if not self.claim_type_id:
            return []

        claim_configs = self.env['tw.work.order.claim'].sudo().search([
            ('claim_type_id', '=', self.claim_type_id.id),
            ('company_id', 'in', [self.company_id.id, False])
        ])
        return claim_configs.mapped('journal_id').ids

    def _prepare_query_rekap_collecting_line_ids(self, wo_ids, claim_journal_ids):
        """
        Query rekap collecting dari account.move + account.move.line,
        filtered by journal_id yang sesuai claim type.
        """
        wo_tuple = str(tuple(wo_ids)).replace(',)', ')')
        journal_tuple = str(tuple(claim_journal_ids)).replace(',)', ')')

        query = f"""
            SELECT 
                wo_count.qty,
                COALESCE(inv_sum.total_jasa, 0) AS total_jasa,
                COALESCE(inv_sum.total_oli, 0) AS total_oli
            FROM (
                SELECT COUNT(wo.id) AS qty, wo.company_id
                FROM tw_work_order wo
                WHERE wo.id IN {wo_tuple}
                GROUP BY wo.company_id
            ) AS wo_count
            FULL OUTER JOIN (
                SELECT 
                    wo.company_id,
                    COALESCE(SUM(aml.price_total) FILTER (WHERE pp.division = 'Service'), 0) AS total_jasa,
                    COALESCE(SUM(aml.price_total) FILTER (WHERE pp.division = 'Sparepart'), 0) AS total_oli
                FROM tw_work_order wo
                INNER JOIN account_move am ON wo.name = am.invoice_origin
                    AND am.move_type = 'out_invoice'
                    AND am.state = 'posted'
                    AND am.journal_id IN {journal_tuple}
                INNER JOIN account_move_line aml ON aml.move_id = am.id
                    AND aml.display_type = 'product'
                    AND aml.price_total > 0
                INNER JOIN product_product pp ON pp.id = aml.product_id
                WHERE wo.id IN {wo_tuple}
                GROUP BY wo.company_id
            ) AS inv_sum ON wo_count.company_id = inv_sum.company_id
            WHERE 1=1
        """
        return query

    def get_rekap_collecting_line_ids(self):
        wo_ids = self.work_order_ids.ids
        if not wo_ids:
            return

        claim_journal_ids = self._get_claim_journal_ids()
        if not claim_journal_ids:
            raise ValidationError(_('Journal untuk Claim Type %s belum di-setting di master Work Order Claim.') % self.claim_type_id.display_name)

        query = self._prepare_query_rekap_collecting_line_ids(wo_ids, claim_journal_ids)
        self._cr.execute(query)
        picks = self._cr.dictfetchall()

        if picks:
            collecting = []
            amount = 0.0
            for value in picks:
                amount += value['total_jasa'] + value['total_oli']
                collecting.append([0, False, value])
            self.write({'collecting_line_ids': collecting, 'amount': amount})
        else:
            raise ValidationError(_('Detail Sudah Tidak Ada.'))
            
    def _get_claim_master(self):
        """
        Ambil master tw.work.order.claim berdasarkan claim_type_id dan company_id.
        Consistent dengan pola yang dipakai di tw_work_order_claim/models/tw_work_order_inherit.py.
        """
        self.ensure_one()
        claim_master = self.env['tw.work.order.claim'].suspend_security().search([
            ('claim_type_id', '=', self.claim_type_id.id),
            ('company_id', 'in', [self.company_id.id, False]),
        ], limit=1)
        if not claim_master:
            raise ValidationError(
                _('Konfigurasi Claim Type "%s" untuk Branch "%s" belum di-setting di master Work Order Claim.')
                % (self.claim_type_id.display_name, self.company_id.name)
            )
        return claim_master

    def _prepare_journal_account(self, account_setting_obj=None):
        """
        Tentukan journal dan account berdasarkan master tw.work.order.claim.
        Journal diambil langsung dari field journal_id pada master claim
        (bukan dari hardcoded account_setting branch).
        """
        claim_master = self._get_claim_master()
        if not claim_master.journal_id:
            raise ValidationError(
                _('Journal pada master Claim Type "%s" belum di-setting.')
                % self.claim_type_id.display_name
            )
        if not claim_master.journal_id.default_debit_account_id:
            raise ValidationError(
                _('Default Debit Account pada journal "%s" (Claim Type "%s") belum di-setting.')
                % (claim_master.journal_id.name, self.claim_type_id.display_name)
            )
        return claim_master.journal_id.id, claim_master.journal_id.default_debit_account_id.id

    def _get_branch_journal_config(self, company_id):
        """
        Kembalikan dict journal_id dan account_id untuk dipakai saat membuat journal entry collecting.
        Journal diambil dari master tw.work.order.claim.
        """
        journal_id, account_id = self._prepare_journal_account()
        return {
            'journal_id': journal_id,
            'account_id': account_id,
        }


    def _prepare_journal_item(self):
        """Mempersiapkan daftar line untuk account.move.line"""
        self.ensure_one()

        oli_total = sum(self.collecting_line_ids.mapped('total_oli'))
        jasa_total = sum(self.collecting_line_ids.mapped('total_jasa'))
        journal_config = self._get_branch_journal_config(self.company_id.id)

        move_lines = []

        # Jika ada OLI
        if oli_total > 0:
            move_lines.append((0, 0, {
                'debit': oli_total,
                'credit': 0,
                'name': self.name + ' OLI',
                'ref': self.name,
                'account_id': journal_config['account_id'],
                'partner_id': self.supplier_id.id,
                'company_id': self.company_id.id,
                'division': self.division,
                'date_maturity': self.due_date,
            }))

        # Jika ada JASA
        if jasa_total > 0:
            move_lines.append((0, 0, {
                'debit': jasa_total,
                'credit': 0,
                'name': self.name + ' JASA',
                'ref': self.name,
                'account_id': journal_config['account_id'],
                'partner_id': self.supplier_id.id,
                'company_id': self.company_id.id,
                'division': self.division,
                'date_maturity': self.due_date,
            }))

        # Ambil claim journal ids (journal yang dipakai pada invoice WO, bukan collecting journal)
        claim_journal_ids = self._get_claim_journal_ids()
        if not claim_journal_ids:
            raise ValidationError(_(
                'Journal untuk Claim Type %s belum di-setting di master Work Order Claim.'
            ) % self.claim_type_id.display_name)

        journal_tuple = str(tuple(claim_journal_ids)).replace(',)', ')')

        # Query untuk ambil receivable lines dari invoice WO (credit side)
        query = f"""
            SELECT
                aml.id,
                aml.account_id,
                aml.debit,
                aml.company_id,
                aml.partner_id,
                aml.division,
                wo.name AS wo_name
            FROM tw_work_order wo
            INNER JOIN account_move am ON wo.name = am.invoice_origin
                AND am.move_type = 'out_invoice'
                AND am.state = 'posted'
                AND am.journal_id IN {journal_tuple}
                AND am.invoice_origin IN (SELECT name FROM tw_work_order WHERE collecting_work_order_id = {self.id})
            INNER JOIN account_move_line aml ON aml.move_id = am.id
                AND aml.debit > 0
            INNER JOIN account_account aa ON aa.id = aml.account_id
                AND aa.reconcile = True
            WHERE wo.collecting_work_order_id = {self.id}
            AND aml.full_reconcile_id IS NULL
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()

        # Tambahkan credit line dari hasil query
        for res in ress:
            move_lines.append((0, 0, {
                'debit': 0,
                'credit': res['debit'],
                'name': res['wo_name'],
                'ref': self.name,
                'account_id': res['account_id'],
                'partner_id': res['partner_id'],
                'company_id': res['company_id'],
                'division': res['division'],
            }))
        return move_lines

    def action_confirm(self):
        self._validate_amount()
        self._create_journal_entries()
        self.write({
            'state': 'posted',
            'confirm_uid': self._uid,
            'confirm_date': self._get_default_date(),
        })

    # 14: private methods
    def _validate_amount(self):
        if self.amount <= 0.0 :
            raise Warning(_('Nilai total collecting kurang dari 0!'))
        if len(self.collecting_line_ids) < 1 :
            raise Warning(_('Tidak ada data detail, klik button Get Detail terlebih dahulu.'))

    def _create_journal_entries(self):
        """Membuat Journal Entry dan line-nya langsung dari _prepare_journal_item"""
        if not self.collecting_line_ids:
            raise ValidationError(_('Isi line terlebih dahulu.'))
        if not self.due_date:
            raise ValidationError(_('Pastikan Due Date sudah terisi !'))

        today = datetime.now()
        period_id = self.env['tw.account.period']._get_current_periods(today).id
        journal_config = self._get_branch_journal_config(self.company_id.id)

        move_exists_obj = self.env['account.move'].sudo().search([
            ('journal_id', '=', journal_config['journal_id']),
            ('name', '=', self.name),
            ('ref', '=', self.name)
        ])

        if not move_exists_obj:
            move_lines = self._prepare_journal_item()
            move_vals = {
                'company_id': self.company_id.id,
                'partner_id': self.supplier_id.id,
                'division': self.division,
                'journal_id': journal_config['journal_id'],
                'move_type': 'entry',
                'period_id': period_id,
                'date': today,
                'name': self.name,
                'ref': self.name,
                'line_ids': move_lines
            }
            move_id = self.env['account.move'].with_company(self.company_id).sudo().create(move_vals)
            self.invoice_id = move_id.id
            move_id.action_open()
            move_id.with_company(self.company_id).sudo().action_post()

            # Reconcile: credit lines dari collecting entry vs receivable lines dari invoice WO KPB
            self._reconcile_collecting_with_wo_invoices(move_id)

    def _reconcile_collecting_with_wo_invoices(self, collecting_move):
        """
        Reconcile credit lines dari journal entry collecting dengan
        receivable lines dari invoice WO (type_id 'CLA', claim_type_id 'KPB').
        Grouping per account_id agar sesuai aturan reconcile Odoo.
        """
        # 1. Ambil credit lines dari collecting entry (yang bukan line debit utama)
        collecting_credit_lines = collecting_move.line_ids.filtered(
            lambda l: l.credit > 0 and l.account_id.reconcile
        )
        if not collecting_credit_lines:
            return

        # 2. Cari semua invoice WO yang terkait collecting ini
        wo_names = self.work_order_ids.mapped('name')
        invoice_wo_ids = self.env['account.move'].sudo().search([
            ('invoice_origin', 'in', wo_names),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ])
        if not invoice_wo_ids:
            return

        # 3. Ambil receivable lines dari invoice WO (debit > 0, account reconcilable, belum full reconcile)
        invoice_receivable_lines = invoice_wo_ids.mapped('line_ids').filtered(
            lambda l: l.debit > 0 and l.account_id.reconcile and not l.full_reconcile_id
        )
        if not invoice_receivable_lines:
            return

        # 4. Gabungkan semua lines yang akan di-reconcile
        all_lines = collecting_credit_lines | invoice_receivable_lines

        # 5. Group by account_id, lalu reconcile per group
        account_ids = all_lines.mapped('account_id')
        for account in account_ids:
            lines_to_reconcile = all_lines.filtered(lambda l: l.account_id == account)
            if lines_to_reconcile:
                lines_to_reconcile.sudo().reconcile()

    def _filter_wo_unreconciled(self, work_orders):
        """
        Filter WO yang invoice receivable line-nya belum ter-reconcile (partial/full).
        Meniru filter lama: aml.reconcile_id IS NULL AND aml.reconcile_partial_id IS NULL
        """
        if not work_orders:
            return work_orders

        wo_names = work_orders.mapped('name')
        invoices = self.env['account.move'].sudo().search([
            ('invoice_origin', 'in', wo_names),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ])

        # Kumpulkan WO name yang invoice receivable line-nya sudah ter-reconcile
        wo_reconciled_names = set()
        for inv in invoices:
            receivable_lines = inv.line_ids.filtered(
                lambda l: l.debit > 0 and l.account_id.reconcile
            )
            # Jika semua receivable lines sudah full/partial reconcile, WO ini tidak boleh diambil
            if receivable_lines and all(l.full_reconcile_id or l.matched_debit_ids or l.matched_credit_ids for l in receivable_lines):
                if inv.invoice_origin:
                    wo_reconciled_names.add(inv.invoice_origin)

        # Exclude WO yang sudah ter-reconcile
        if wo_reconciled_names:
            work_orders = work_orders.filtered(lambda wo: wo.name not in wo_reconciled_names)

        return work_orders

    @api.model_create_multi
    def create(self,vals_list):
        for values in vals_list:
            if values.get('company_id'):
                branch_src = self.env['res.company'].suspend_security().search([('id','=',values['company_id'])],limit=1)
            values['name'] = self.env['ir.sequence'].get_sequence_code('CK', str(branch_src.code))
        collecting_kpb = super(TwWorkOrderCollecting,self).create(vals_list)
        return collecting_kpb 
    
    
    def write(self, values):
        if 'work_order_ids' not in values:
            for key in values:
                if key in ('company_id', 'claim_type_id', 'start_date', 'end_date'):
                    values.update({'work_order_ids': [(5, 0)], 'collecting_line_ids': [(5, 0)], 'amount': 0})
                    break
        return super(TwWorkOrderCollecting, self).write(values)
    
    def unlink(self, context=None):
        for tc in self :
            if tc.state != 'draft' :
                raise ValidationError(_('Transaksi yang berstatus selain Draft tidak bisa dihapus.'))
        return super(TwWorkOrderCollecting, self).unlink()
    
    @api.model
    def copy(self):
        raise ValidationError(_('Transaksi ini tidak dapat diduplikat.'))
        return super(TwWorkOrderCollecting, self).copy()
    
class TwWorkOrderCollectingLine(models.Model):
    _name = "tw.work.order.collecting.line"
    _description = "TW Work Order Collecting Line"

    # 7: defaults methods

    # 8: fields
    categ = fields.Char('Category')
    qty = fields.Integer('Qty')
    jasa = fields.Float('Jasa')
    oli = fields.Float('Oli')
    total_jasa = fields.Float('Total Jasa')
    total_oli = fields.Float('Total Oli')

    # 9: relation fields
    collecting_work_order_id = fields.Many2one('tw.work.order.collecting')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods