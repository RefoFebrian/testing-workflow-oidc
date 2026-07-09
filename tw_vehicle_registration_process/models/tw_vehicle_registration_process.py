# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Posted'),
    ('cancel', 'Cancelled'),
]


class TwVehicleRegistrationProcess(models.Model):
    _name = "tw.vehicle.registration.process"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Proses STNK"
    _order = "id desc"

    # 8: fields
    name = fields.Char(string="Name", compute='_compute_name', default='New', copy=False, readonly=True, store=True)
    confirm_date = fields.Datetime('Posted on')
    cancel_date = fields.Datetime('Cancelled on')
    date = fields.Date(string='Date', default=fields.Date.today())
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')

    # 9: relation fields
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    company_id = fields.Many2one('res.company', string='Branch', required=True, domain=[('parent_id', '!=', False)], default=lambda self: self.env.company)
    available_biro_jasa_ids = fields.Many2many('res.partner', compute='_compute_available_biro_jasa_ids')
    biro_jasa_id = fields.Many2one(comodel_name='res.partner', string='Biro Jasa', domain="[('id', 'in', available_biro_jasa_ids)]", required=True, tracking=True)
    old_biro_jasa_id = fields.Many2one(comodel_name='res.partner', string='Old Biro Jasa')
    registration_process_line_ids = fields.One2many('tw.vehicle.registration.process.line', 'registration_process_id', string="STNK Process Line", copy=True)
    available_lot_ids = fields.Many2many('stock.lot', string='Domain Lot', compute='_compute_available_lot_ids')

    @api.depends('company_id')
    def _compute_available_biro_jasa_ids(self):
        for rec in self:
            if rec.company_id and rec.company_id.branch_setting_id:
                birojasa_settings = rec.company_id.branch_setting_id.birojasa_setting_ids
                rec.available_biro_jasa_ids = birojasa_settings.mapped('biro_jasa_id').ids
            else:
                rec.available_biro_jasa_ids = False
    change_biro_jasa_journal_count = fields.Integer(
        string='Journal Entries Ganti BiJas',
        compute='_compute_change_biro_jasa_journal_count'
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & onchange methods
    @api.depends('company_id', 'biro_jasa_id')
    def _compute_available_lot_ids(self):
        for rec in self:
            if not rec.company_id or not rec.biro_jasa_id:
                rec.available_lot_ids = False
                continue

            # Get all lots that match the criteria
            query = """
                SELECT sl.id 
                FROM stock_lot sl
                WHERE sl.company_id = %s
                AND sl.vehicle_document_receive_id IS NOT NULL
                AND sl.registration_process_id IS NULL
                AND sl.biro_jasa_id = %s
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_vehicle_registration_process_line rpl
                    JOIN tw_vehicle_registration_process rp ON rpl.registration_process_id = rp.id
                    WHERE rpl.lot_id = sl.id 
                    AND rpl.state != 'cancel'
                    AND rp.state NOT IN ('done', 'cancel')
                    AND rp.id != %s
                )
            """
            params = (rec.company_id.id, rec.biro_jasa_id.id, rec.id or 0)
            self._cr.execute(query, params)
            lot_ids = [row[0] for row in self._cr.fetchall()]
            rec.available_lot_ids = [(6, 0, lot_ids)] if lot_ids else False

    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                # Cegah penarikan sequence di level UI (Onchange/Transient Record) agar tidak bolong/loncat
                if isinstance(rec.id, models.NewId) or not rec.id:
                    rec.name = 'New'
                elif rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('BJ', str(rec.company_id.code))



    def _compute_change_biro_jasa_journal_count(self):
        """Hitung jumlah Journal Entries yang dibuat dari proses Ganti Biro Jasa.

        Journal diidentifikasi dari accure_bbn_move_id pada lot yang terkait,
        ditambah journal reverse-nya (ref mengandung nama registrasi).
        """
        for rec in self:
            if not rec.name or rec.name == 'New' or not rec.old_biro_jasa_id:
                rec.change_biro_jasa_journal_count = 0
                continue
            lot_ids = rec.registration_process_line_ids.mapped('lot_id')
            current_move_ids = lot_ids.mapped('accure_bbn_move_id').ids
            reverse_moves = self.env['account.move'].sudo().search([
                ('move_type', '=', 'entry'),
                ('ref', 'ilike', rec.name),
                ('company_id', '=', rec.company_id.id),
            ])
            all_ids = list(set(current_move_ids + reverse_moves.ids))
            rec.change_biro_jasa_journal_count = len(all_ids)

    @api.onchange('company_id', 'biro_jasa_id')
    def onchange_company(self):
        self.registration_process_line_ids = False
        registration_process_line_ids = []
        transaction_id = ''
        if self._origin.id:
            transaction_id = f" AND rp.id != {self._origin.id}"
        if self.company_id and self.biro_jasa_id:
            query = """
                SELECT sl.id 
                FROM stock_lot sl
                WHERE sl.company_id = %s
                AND sl.vehicle_document_receive_id IS NOT NULL
                AND sl.registration_process_id IS NULL
                AND sl.biro_jasa_id = %s
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_vehicle_registration_process_line rpl
                    JOIN tw_vehicle_registration_process rp ON rpl.registration_process_id = rp.id
                    WHERE rpl.lot_id = sl.id 
                    AND rp.state NOT IN ('done', 'cancel')
                    AND rpl.state != 'cancel'
                    %s
                )
            """
            params = (self.company_id.id, self.biro_jasa_id.id, transaction_id)
            self._cr.execute(query, params)
            lot_ids = [row[0] for row in self._cr.fetchall()]

            for lot_id in lot_ids:
                registration_process_line_ids.append((0, 0, {
                    'lot_id': lot_id
                }))
        self.registration_process_line_ids = registration_process_line_ids

    # 12: override base methods
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.validate_order()
        return res

    def write(self, vals):
        res = super(TwVehicleRegistrationProcess, self).write(vals)
        self.validate_order()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You cannot delete data that is not in draft status."))

    # 13: action methods
    def action_confirm(self):
        for rec in self.filtered(lambda r: r.state == 'draft'):
            rec.write({
                'state': 'done',
                'confirm_uid': self.env.user.id,
                'confirm_date': datetime.now(),
            })
            rec.registration_process_line_ids.suspend_security().write({
                'state': 'done',
            })
            lot_ids = rec.registration_process_line_ids.mapped('lot_id')
            lot_ids.write({
                'registration_process_id': rec.id,
                'registration_process_date': rec.date,
                'document_state': 'registration_process',
                'biro_jasa_id': rec.biro_jasa_id.id
            })

            # Jika ada lot yang partner aslinya di jurnal accrue BBN berbeda dengan biro_jasa_id yang terpilih saat confirm, proses pergantian jurnal
            lots_with_changes = lot_ids.filtered(
                lambda l: l.accure_bbn_move_id and l.accure_bbn_move_id.state == 'posted' and l.accure_bbn_move_id.partner_id != rec.biro_jasa_id
            )
            if lots_with_changes:
                rec._process_accrue_bbn_change(lots_with_changes, rec.biro_jasa_id)

    def action_cancel(self):
        for rec in self.filtered(lambda r: r.state == 'done'):
            lots = rec.registration_process_line_ids.lot_id
            rec.write({
                'state': 'cancel',
                'cancel_uid': self.env.user.id,
                'cancel_date': datetime.now(),
            })
            if lots:
                lots.write({
                    'biro_jasa_id': rec.old_biro_jasa_id.id if rec.old_biro_jasa_id else rec.biro_jasa_id.id
                })

    def action_print_out_registration(self):
        self.ensure_one()
        return self.env.ref('tw_vehicle_registration_process.action_print_out_registration').report_action(self)

    def action_change_biro_jasa(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.change.birojasa.wizard',
            'name': 'Change Biro Jasa',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_old_biro_jasa_id': self.biro_jasa_id.id,
                'active_id': self.id,
                'default_lot': self.registration_process_line_ids.lot_id.ids,
            },
        }

    def action_view_change_biro_jasa_journals(self):
        """Buka listing Journal Entries yang dihasilkan dari proses Ganti Biro Jasa."""
        self.ensure_one()
        lot_ids = self.registration_process_line_ids.mapped('lot_id')
        current_move_ids = lot_ids.mapped('accure_bbn_move_id').ids
        reverse_moves = self.env['account.move'].sudo().search([
            ('move_type', '=', 'entry'),
            ('ref', 'ilike', self.name),
            ('company_id', '=', self.company_id.id),
        ])
        all_ids = list(set(current_move_ids + reverse_moves.ids))

        return {
            'name': _('Journal Entries Ganti Biro Jasa - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', all_ids)],
            'context': {
                'default_move_type': 'entry',
                'search_default_group_by_partner': 1,
            },
        }

    # 14: private methods
    def validate_order(self):
        """Validasi kelengkapan engine line sebelum create/write."""
        for rec in self:
            if not rec.registration_process_line_ids:
                raise ValidationError(_('Please input engine line.'))
            for line in rec.registration_process_line_ids:
                other_line_id = self.env['tw.vehicle.registration.process.line'].search([
                    ('lot_id', '=', line.lot_id.id),
                    ('id', '!=', line.id),
                    ('registration_process_id.state', '!=', 'cancel'),
                    ('state', '!=', 'cancel'),
                ], limit=1)
                if other_line_id:
                    raise ValidationError(_(f'Engine number {line.lot_id.name} has been processed in'
                                            f' {other_line_id.registration_process_id.name}.'))
                if not line.lot_id.vehicle_document_receive_id:
                    raise ValidationError(_(f'Engine number {line.lot_id.name} has not been received (Penerimaan Faktur).'))

    def _process_accrue_bbn_change(self, lot_ids, new_biro_jasa):
        """Buat jurnal balikan dan jurnal baru untuk lot yang mengalami pergantian biro jasa.

        Args:
            lot_ids: stock.lot recordset yang butuh pergantian jurnal
            new_biro_jasa: res.partner (biro_jasa_id yang aktif saat di-post)
        """
        self.ensure_one()
        account_conf = self._get_account_conf()
        
        for lot in lot_ids:
            old_move = lot.accure_bbn_move_id
            old_biro_jasa = old_move.partner_id

            self._create_reverse_accrue_bbn(old_move, account_conf, old_biro_jasa, new_biro_jasa)
            new_move = self._create_new_accrue_bbn(old_move, account_conf, new_biro_jasa)
            
            lot.suspend_security().write(
                {
                    'accure_bbn_move_id': new_move.id,
                    'accrue_bbn_move_line_ids' : [(6, 0, new_move.line_ids.filtered(lambda x: x.credit > 0).ids)]
                }
            )

    def _get_account_conf(self):
        """Ambil dan validasi konfigurasi akun dari Branch Setting.

        Returns:
            account.setting record
        """
        self.ensure_one()
        account_conf = self.company_id.branch_setting_id.account_setting_id
        if not account_conf:
            raise Warning(_(
                "Account Setting belum dikonfigurasi untuk cabang %s."
            ) % self.company_id.name)
        if not account_conf.journal_dso_purchase_bbn_id:
            raise Warning(_(
                "Journal Pembelian BBN belum dikonfigurasi di Account Setting cabang %s."
            ) % self.company_id.name)
        return account_conf

    def _create_reverse_accrue_bbn(self, old_move, account_conf, old_biro_jasa, new_biro_jasa):
        """Buat journal entry balikan (reverse) dari Accrue BBN lama."""
        journal = account_conf.journal_dso_purchase_bbn_id
        prefix = self.company_id.code

        reverse_line_vals = self._prepare_reverse_move_lines(old_move, old_biro_jasa)
        reverse_vals = self._prepare_move_vals(journal, prefix, old_move.ref, old_biro_jasa, reverse_line_vals)

        reverse_move = self.env['account.move'].suspend_security().with_company(self.company_id).create(reverse_vals)
        reverse_move.suspend_security().action_post()
        return reverse_move

    def _create_new_accrue_bbn(self, old_move, account_conf, new_biro_jasa):
        """Buat journal entry Accrue BBN baru dengan Biro Jasa yang baru."""
        journal = account_conf.journal_dso_purchase_bbn_id
        prefix = self.company_id.code

        new_line_vals = self._prepare_new_move_lines(old_move, new_biro_jasa)
        new_vals = self._prepare_move_vals(journal, prefix, old_move.ref, new_biro_jasa, new_line_vals)

        new_move = self.env['account.move'].suspend_security().with_company(self.company_id).create(new_vals)
        new_move.suspend_security().action_post()
        return new_move

    def _prepare_move_vals(self, journal, prefix, ref, partner, line_vals):
        """Siapkan dict nilai untuk pembuatan account.move."""
        return {
            'move_type': 'entry',
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'division': self.division,
            'partner_id': partner.id,
            'date': fields.Date.today(),
            'ref': ref,
            'name': self.env['ir.sequence'].get_sequence_code(journal.code, prefix),
            'line_ids': line_vals,
        }

    def _prepare_reverse_move_lines(self, old_move, partner):
        """Balik posisi debit/credit dari setiap baris journal lama."""
        line_vals = []
        for line in old_move.line_ids:
            line_vals.append((0, 0, {
                'account_id': line.account_id.id,
                'partner_id': partner.id,
                'name': line.name,
                'debit': line.credit,   # dibalik
                'credit': line.debit,   # dibalik
                'currency_id': line.currency_id.id,
                'amount_currency': -line.amount_currency,
                'company_id': self.company_id.id,
                'division': line.division or self.division,
            }))
        return line_vals

    def _prepare_new_move_lines(self, old_move, partner):
        """Salin posisi debit/credit dari journal lama dengan partner baru."""
        line_vals = []
        for line in old_move.line_ids:
            line_vals.append((0, 0, {
                'account_id': line.account_id.id,
                'partner_id': partner.id,
                'name': line.name,
                'debit': line.debit,
                'credit': line.credit,
                'currency_id': line.currency_id.id,
                'amount_currency': line.amount_currency,
                'company_id': self.company_id.id,
                'division': line.division or self.division,
            }))
        return line_vals
