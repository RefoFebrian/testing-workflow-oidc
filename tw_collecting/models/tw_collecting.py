# 1: imports of python lib
import calendar
from datetime import datetime, date

# 2: import of known third party lib

# 3: imports of odoo
from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError as Warning

# 4: imports from odoo modules
from odoo.tools import float_compare

# 5: local imports

# 6: Import of unknown third party lib

class TwCollecting(models.Model):
    """Model for managing AR/AP collection entries.
    
    This model handles the creation and management of accounts receivable/payable
    collection entries with proper state management and workflow.
    """
    _name = "tw.collecting"
    _description = 'Collecting AR/AP'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True
    _order = "id desc"

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('confirm','Confirmed'),
        ('cancel','Cancelled')
    ]

    # 7: defaults methods
    
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False  

    def _get_default_date(self):
        return date.today()

    def _get_default_date_start(self):
        """Get first day of current month as default start date."""
        now = self._get_default_date()
        return datetime(now.year, now.month, 1)

    def _get_default_date_end(self):
        """Get last day of current month as default end date."""
        now = self._get_default_date()
        return datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1])

    # 8: fields
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    date = fields.Date(string='Date', default=_get_default_date, tracking=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    state = fields.Selection(selection=STATE_SELECTION, string='Status', default='draft', copy=False, tracking=True)
    type = fields.Selection(selection=[('asset_receivable', 'Receivable'), ('liability_payable', 'Payable')], string='Type', default='asset_receivable', tracking=True)
    amount_type = fields.Selection(selection=[('all','Debits & Credits'),('debit', 'Debit'), ('credit', 'Credit')], string='Amount Type', default='all', tracking=True)
    date_start = fields.Date(string='Effective Date', default=_get_default_date_start, tracking=True)
    date_end = fields.Date(string='Date End', default=_get_default_date_end, tracking=True)
    date_maturity = fields.Date(string='Due Date', tracking=True)
    description = fields.Char(string='Description', tracking=True)
    amount = fields.Float(string='Amount', tracking=True, digits=(16, 2))
    is_branch_menu = fields.Boolean('is branch menu', default=False)
    
    # Audit Trail
    confirm_date = fields.Datetime(string='Confirmed on', copy=False)
    confirm_uid = fields.Many2one('res.users', string="Confirmed by", copy=False)
    cancel_date = fields.Datetime(string='Cancelled on', copy=False)
    cancel_uid = fields.Many2one('res.users', string="Cancelled by", copy=False)

    # 9: Relational Fields
    company_id = fields.Many2one('res.company', string="Branch", default=_get_default_branch, tracking=True, ondelete='restrict')
    currency_id = fields.Many2one("res.currency", string="Currency", related="company_id.currency_id", readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True, ondelete='restrict')
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type', 'in', ('bank', 'cash'),('company_id','parent_of',company_id)]")
    move_line_ids = fields.Many2many('account.move.line', 'tw_collecting_move_line_rel', 'collecting_id', 'move_line_id', string='Journal Items', copy=False)
    available_account_ids = fields.Many2many(comodel_name='account.account',compute='_compute_available_account_ids')
    account_id = fields.Many2one('account.account', string='Account', tracking=True)
    
    collected_move_id = fields.Many2one('account.move', string='Journal Entry', copy=False, ondelete='restrict')
    collected_move_line_ids = fields.One2many("account.move.line", related="collected_move_id.line_ids", string="Collected Journal Items", readonly=True)

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            if record.id and not record.name and record.state:
                seq_name = self.env['ir.sequence'].with_company(record.company_id).get_sequence_code('CL', record.company_id.code)
                record.name = seq_name

    @api.depends('company_id')
    def _compute_available_account_ids(self):
        for record in self:
            domain = [('id', 'in', [])]
            if record.company_id:
                domain = ['|', ('company_ids', 'in', record.company_id.id), ('company_ids', 'parent_of', record.company_id.id)]
            payment_type = 'collecting'
            if record.is_branch_menu:
                payment_type = 'collecting_branch'
            account_filter_domain = self.env['tw.account.filter'].get_account_domain(payment_type)
            if account_filter_domain:
                domain += account_filter_domain
            record.available_account_ids = self.env['account.account'].search(domain)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.account_id = False
        self.journal_id = False

    @api.onchange('company_id', 'division', 'partner_id', 'date', 'date_start', 'date_end', 'type', 'amount_type', 'account_id', 'journal_id')
    def _onchange_reset_line(self):
        self.move_line_ids = False
        self.amount = 0.0

    @api.onchange('type')
    def _onchange_type(self):
        self.account_id = False
    
    @api.onchange('date_maturity')
    def _onchange_date_maturity(self):
        now = datetime.now().date()
        if self.date_maturity:
            if self.date_maturity < now:
                self.date_maturity = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def write(self, values):
        return super().write(values)

    def unlink(self):
        """Prevent deletion of records not in draft state."""
        non_draft = self.filtered(lambda r: r.state != 'draft')
        if non_draft:
            raise Warning(_('Only draft records can be deleted. Please cancel the record first.'))
        return super().unlink()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """Prevent copying of records."""
        self.ensure_one()
        raise Warning(_('Duplicating collecting entries is not allowed.'))

    # 13: action methods
    def action_get_detail(self):
        """Retrieve move lines based on current filters."""
        self.ensure_one()
        
        # Build domain for move line search
        domain = [
            ('company_id', '=', self.company_id.id),
            ('division', '=', self.division),
            ('partner_id', '=', self.partner_id.id),
            ('account_id', '=', self.account_id.id),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('move_id.state', '=', 'posted'),
            ('reconciled', '=', False),
            ('full_reconcile_id', '=', False)
        ]
        
        if self.journal_id:
            domain.append(('move_id.journal_id', '=', self.journal_id.id))

        if self.amount_type != 'all' :
            if self.amount_type == 'debit' :
                domain.append(('debit', '>', 0))
            else :
                domain.append(('credit', '>', 0))
            
        # Search for move lines
        move_lines = self.env['account.move.line'].search(domain)
        
        if not move_lines:
            raise Warning(_('Tidak ada journal items ditemukan untuk kriteria yang diberikan.'))
            
        # Calculate total amount
        total_amount = sum(line.debit + line.credit for line in move_lines)
        
        # Update record with found move lines and calculated amount
        self.write({
            'move_line_ids': [(6, 0, move_lines.ids)],
            'amount': total_amount,
            'date': self._get_default_date()
        })

    def action_confirm(self):
        self.ensure_one()
        self._validate_amount()
        move_id = self._create_account_move()

        self.write({
            'collected_move_id': move_id.id,
            'state': 'confirm',
            'confirm_date': datetime.now(),
            'confirm_uid': self._uid,
        })
        
    # 14: private methods
    def _validate_amount(self):
        if self.amount <= 0.0 :
            raise Warning(_('Nilai total collecting kurang dari 0!'))
        if len(self.move_line_ids) < 1 :
            raise Warning(_('Tidak ada data detail, klik button Get Detail terlebih dahulu.'))

        config = self.company_id.branch_setting_id
        if not config :
            raise Warning(_('Tidak ditemukan konfigurasi cabang %s, silahkan konfigurasi terlebih dahulu.'%self.company_id.code))
        account_setting = config.account_setting_id
        if not account_setting :
            raise Warning(_('Tidak ditemukan konfigurasi akun cabang %s, silahkan konfigurasi terlebih dahulu.'%self.company_id.code))
        journal_id = account_setting.journal_collecting_id.id
        if not journal_id :
            raise Warning(_('Konfigurasi Journal collecting di cabang %s belum di setting, silahkan konfigurasi terlebih dahulu.'%self.company_id.code))

    def _create_account_move(self):
        """Create account move for collecting entry."""
        self.ensure_one()
       
        today = self._get_default_date()
        period_id = self.env['tw.account.period']._get_current_periods(today).id
        journal_id = self.company_id.branch_setting_id.account_setting_id.journal_collecting_id.id


        move_line_vals = []
        total_amount = 0.0
        warning = ""
        for move_line in self.move_line_ids :
            if move_line.reconciled:
                warning += "- %s \r\n" % move_line.name
            
            total_amount += move_line.debit - move_line.credit
            
            move_line_vals.append({
                'company_id': move_line.company_id.id,
                'debit': move_line.credit,
                'credit': move_line.debit,
                'name': 'Collecting %s' % move_line.name,
                'ref': move_line.ref,
                'account_id': move_line.account_id.id,
                'partner_id': move_line.partner_id.id,
                'division': self.division,
                'date_maturity': today,
                })
        
        if warning != "" :
            raise Warning("Transaksi berikut sudah di reconcile (sebagian / penuh):\r\n %s " % warning)

        collecting_vals = {
            'company_id': self.company_id.id,
            'debit': total_amount if total_amount > 0 else 0,
            'credit': abs(total_amount) if total_amount < 0 else 0,
            'name': self.description if self.description else self.name,
            'ref': self.name,
            'account_id': self.account_id.id,
            'partner_id': self.partner_id.id,
            'division': self.division,
            'date_maturity': self.date_maturity if self.date_maturity else today,
        }
        move_line_vals.append(collecting_vals)

        move_id = self.env['account.move'].sudo().create({
            'division': self.division,
            'company_id': self.company_id.id,
            'journal_id': journal_id,
            'period_id': period_id,
            'date': today,
            'name': self.name,
            'ref': self.name,
            'line_ids': [
                Command.create(line)
                for line in move_line_vals
            ],
        }) 
        move_id.sudo().action_post()

        collecting_move_line = move_id.line_ids.filtered(lambda x: x.name == collecting_vals['name'] and x.account_id.id == collecting_vals['account_id'] and round(x.debit, 2) == round(collecting_vals['debit'], 2) and round(x.credit, 2) == round(collecting_vals['credit'], 2))
        if len(collecting_move_line) != 1:
            raise Warning('Gagal Confirm. Ditemukan lebih dari 1 line collecting yang sama.')

        to_reconcile_ids = move_id.line_ids.filtered(lambda x: x.id != collecting_move_line.id)
        if len(to_reconcile_ids) != len(self.move_line_ids):
            raise Warning('Gagal Confirm. Jumlah line collecting yang akan di reconcile tidak sesuai.')

        to_reconcile_ids += self.move_line_ids
        to_reconcile_ids.sudo().reconcile()

        return move_id
        