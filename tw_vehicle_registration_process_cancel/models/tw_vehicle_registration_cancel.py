# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError


# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwVehicleRegistrationProcessCancel(models.Model):
    _name = "tw.registration.process.cancel"
    _description = 'Proses STNK Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _order = 'id desc'

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return fields.Date.today()

    # 8: fields
    name = fields.Char(string="Name", compute='_compute_name', store=True, default='New', copy=False)
    note = fields.Text(string="Note", readonly=True)
    # 9: relation fields
    vehicle_registration_process_id = fields.Many2one(
        'tw.vehicle.registration.process', 
        'Proses STNK'
    )
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')
    vehicle_registration_cancel_line_ids = fields.One2many('tw.registration.process.cancel.line', 'cancel_id', 'Cancel Line')
    available_lot_ids = fields.Many2many('stock.lot', string='Domain Lot', compute='_compute_available_lot_ids')
    available_process_ids = fields.Many2many(
        'tw.vehicle.registration.process',
        string='Available Processes',
        compute='_compute_available_process_ids'
    )

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_available_process_ids(self):
        """Compute available registration processes that have cancellable lots."""
        for record in self:
            available_processes = []
            
            if record.company_id:
                # Query for processes with cancellable lots
                self._cr.execute("""
                    SELECT DISTINCT rp.id
                    FROM tw_vehicle_registration_process rp
                    INNER JOIN tw_vehicle_registration_process_line rl ON rl.registration_process_id = rp.id
                    INNER JOIN stock_lot sl ON sl.id = rl.lot_id
                    WHERE rp.company_id = %s
                    AND rp.state = 'done'
                    AND rl.state != 'cancel'
                    AND (sl.vehicle_ownership_receipt_id IS NULL 
                         OR sl.vehicle_registration_receipt_id IS NULL 
                         OR sl.notice_receipt_id IS NULL 
                         OR sl.plate_receipt_id IS NULL)
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tw_registration_process_cancel_line cl
                        JOIN tw_registration_process_cancel c ON cl.cancel_id = c.id
                        LEFT JOIN tw_cancellation tc ON c.cancellation_id = tc.id
                        WHERE cl.lot_id = sl.id 
                        AND tc.state != 'confirmed'
                        AND c.id != %s
                    )
                """, (record.company_id.id, record.id or 0))
                available_processes = [row[0] for row in self._cr.fetchall()]
            
            record.available_process_ids = [(6, 0, available_processes)]
    
    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if hasattr(models, 'NewId') and isinstance(rec.id, models.NewId) or not rec.id:
                    rec.name = 'New'
                    continue
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('CPS', str(rec.company_id.code))
    
    @api.depends('vehicle_registration_process_id')
    def _compute_available_lot_ids(self):
        for record in self:
            record.available_lot_ids = False
            if record.vehicle_registration_process_id:
                # Query to get lots that are in the current registration process
                # and not used in other active transactions
                query = """
                    SELECT sl.id 
                    FROM stock_lot sl
                    LEFT JOIN tw_vehicle_registration_process_line rl ON rl.registration_process_id = sl.registration_process_id
                    WHERE sl.registration_process_id = %s
                    AND (sl.vehicle_ownership_receipt_id is null or sl.vehicle_registration_receipt_id is null or sl.notice_receipt_id is null or sl.plate_receipt_id is null)
                    AND sl.id IN %s
                    AND rl.state !='cancel'
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM tw_registration_process_cancel_line cl
                        JOIN tw_registration_process_cancel c ON cl.cancel_id = c.id
                        LEFT JOIN tw_cancellation tc ON c.cancellation_id = tc.id
                        WHERE cl.lot_id = sl.id 
                        AND tc.state != 'confirmed'
                        AND c.id != %s
                    )
                """
                lot_ids = tuple(record.vehicle_registration_process_id.registration_process_line_ids.mapped('lot_id').ids)
                if lot_ids:  # Only execute query if there are lot_ids to check
                    params = (record.vehicle_registration_process_id.id, lot_ids, record.id or 0)
                    self._cr.execute(query, params)
                    valid_lot_ids = [row[0] for row in self._cr.fetchall()]
                    record.available_lot_ids = [(6, 0, valid_lot_ids)] if valid_lot_ids else False
                
                if record.vehicle_registration_process_id.old_biro_jasa_id and record.vehicle_registration_process_id.old_biro_jasa_id != record.vehicle_registration_process_id.biro_jasa_id:
                    record.note = "Tindakan ini akan membatalkan Pergantian ke (" + record.vehicle_registration_process_id.biro_jasa_id.name + ") Proses pengurusan STNK akan dikembalikan ke penanggung jawab awal (" + record.vehicle_registration_process_id.old_biro_jasa_id.name + ")"

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.vehicle_registration_process_id = False

    @api.onchange('vehicle_registration_process_id')
    def _onchange_vehicle_registration_process_id(self):
        self.transaction_name = False
        self.vehicle_registration_cancel_line_ids = False
        if self.vehicle_registration_process_id:
            self.transaction_name = self.vehicle_registration_process_id.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['date'] = self._get_default_date()
        return super().create(vals_list)
    
    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You cannot delete data that is not in draft status."))

    def action_confirm(self):
        self._validity_check()
        for line in self.vehicle_registration_cancel_line_ids:
            if self.vehicle_registration_process_id:
                # Cancel process lines for this lot
                process_lines = self.vehicle_registration_process_id.registration_process_line_ids.filtered(
                    lambda l: l.lot_id == line.lot_id and l.state != 'cancel'
                )
                if process_lines:
                    process_lines.action_cancel()
            
        # Cancel the receipt if all lines are cancelled
        if self.vehicle_registration_process_id:
            all_lines_cancelled = all(
                line.state == 'cancel'
                for line in self.vehicle_registration_process_id.registration_process_line_ids
            )
            if all_lines_cancelled:
                self.vehicle_registration_process_id.action_cancel()
        
            # cancel birojasa change: revert biro jasa dan balikan journal accrue BBN
            if self.note and self.vehicle_registration_process_id.old_biro_jasa_id:
                process = self.vehicle_registration_process_id
                new_biro_jasa = process.biro_jasa_id       # B (saat ini aktif)
                old_biro_jasa = process.old_biro_jasa_id  # A (semula)
                lot_ids = self.vehicle_registration_cancel_line_ids.mapped('lot_id')

                # Balikan journal accrue BBN: B → A
                self._reverse_accrue_bbn_biro_jasa(process, lot_ids, new_biro_jasa, old_biro_jasa)

                # Kembalikan biro jasa di process ke semula
                process.write({'biro_jasa_id': old_biro_jasa.id})
                lot_ids.suspend_security().write({'biro_jasa_id': old_biro_jasa.id})
        
        return self.cancellation_id.action_confirm()


    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)

    def action_request_approval(self):
        return super().action_request_approval(value=5)
    
    def _validity_check(self):
        """Validate STNK process cancellation with optimized checks."""
        for rec in self:
            if not rec.vehicle_registration_process_id:
                continue

            # Early exit if no lines
            if not rec.vehicle_registration_cancel_line_ids:
                raise ValidationError(_('Please add at least one lot to cancel.'))

            # Check for existing billings
            billed_lots = rec.env['stock.lot'].search([
                ('id', 'in', rec.vehicle_registration_cancel_line_ids.mapped('lot_id').ids),
                ('birojasa_billing_id', '!=', False)
            ])
            if billed_lots:
                lot_names = ', '.join(billed_lots.mapped('name'))
                raise UserError(_('Cannot cancel lots with existing billing: %s') % lot_names)

            # Get all lots and check for duplicates
            cancel_lots = rec.vehicle_registration_cancel_line_ids.mapped('lot_id')
            if len(cancel_lots) != len(set(cancel_lots)):
                dupes = [lot.name for lot in cancel_lots 
                        if cancel_lots.filtered(lambda l: l == lot).mapped('id').count(lot.id) > 1]
                raise ValidationError(_(
                    f'Duplicate lots found: {", ".join(set(dupes))}. '
                    'Please remove duplicates.'
                ))

            # Check process state
            if rec.vehicle_registration_process_id.state == 'cancel':
                raise ValidationError(_(
                    f'Registration process {rec.vehicle_registration_process_id.name} is already cancelled.'
                ))

            # Get process lots once
            process_lots = rec.vehicle_registration_process_id.registration_process_line_ids.lot_id
            if not process_lots:
                return

            # Check lot validity in one pass
            invalid_lots = rec.vehicle_registration_cancel_line_ids.filtered(
                lambda l: (
                    l.lot_id not in process_lots or
                    l.lot_id.vehicle_ownership_receipt_id or
                    l.lot_id.vehicle_registration_receipt_id or
                    l.lot_id.notice_receipt_id or
                    l.lot_id.plate_receipt_id
                )
            )

            # Check active cancellations in batch
            lot_ids = tuple(cancel_lots.ids)
            if lot_ids:
                self._cr.execute("""
                    SELECT cl.lot_id 
                    FROM tw_registration_process_cancel_line cl
                    JOIN tw_registration_process_cancel c ON cl.cancel_id = c.id
                    LEFT JOIN tw_cancellation tc ON c.cancellation_id = tc.id
                    WHERE cl.lot_id IN %s 
                    AND tc.state != 'confirmed'
                    AND c.id != %s
                """, (lot_ids, rec.id or 0))
                
                active_lot_ids = {row[0] for row in self._cr.fetchall()}
                invalid_lots |= rec.vehicle_registration_cancel_line_ids.filtered(
                    lambda l: l.lot_id.id in active_lot_ids
                )

            # Raise error if any invalid lots
            if invalid_lots:
                error_messages = []
                for lot in invalid_lots.mapped('lot_id'):
                    if lot not in process_lots:
                        message = f"- {lot.name}: Not in process"
                    elif any([
                        lot.vehicle_ownership_receipt_id,
                        lot.vehicle_registration_receipt_id,
                        lot.notice_receipt_id,
                        lot.plate_receipt_id
                    ]):
                        message = f"- {lot.name}: Already received"
                    else:
                        message = f"- {lot.name}: In another cancellation"
                    error_messages.append(message)
                
                raise ValidationError('The following lots cannot be cancelled:\n' + '\n'.join(error_messages))
    
    def validate_order(self):
        self.ensure_one()
        self._validity_check()
        return super().validate_order()

    def _reverse_accrue_bbn_biro_jasa(self, process, lot_ids, from_biro_jasa, to_biro_jasa):
        """Balik journal Accrue BBN dari from_biro_jasa ke to_biro_jasa untuk setiap lot.

        Alur per lot:
        1. Ambil accure_bbn_move_id (journal aktif saat ini, partner = from_biro_jasa)
        2. Buat jurnal balikan (debit/credit dibalik, partner tetap from_biro_jasa)
        3. Buat jurnal baru dengan nilai sama, partner = to_biro_jasa
        4. Update accure_bbn_move_id di lot ke jurnal baru

        Args:
            process: tw.vehicle.registration.process record
            lot_ids: stock.lot recordset yang terdampak
            from_biro_jasa: res.partner biro jasa yang sedang aktif (akan dibalik)
            to_biro_jasa: res.partner biro jasa tujuan (journal baru dibuat untuknya)
        """
        account_conf = self._get_account_conf_cancel(process)
        for lot in lot_ids:
            current_move = lot.accure_bbn_move_id
            if not current_move or current_move.state != 'posted':
                continue
            self._create_reverse_move(current_move, account_conf, process, from_biro_jasa, to_biro_jasa)
            new_move = self._create_new_move(current_move, account_conf, process, to_biro_jasa)
            lot.suspend_security().write({'accure_bbn_move_id': new_move.id})

    def _get_account_conf_cancel(self, process):
        """Ambil dan validasi konfigurasi akun dari Branch Setting.

        Args:
            process: tw.vehicle.registration.process record

        Returns:
            account.setting record
        """
        account_conf = process.company_id.branch_setting_id.account_setting_id
        if not account_conf:
            raise ValidationError(_(
                "Account Setting belum dikonfigurasi untuk cabang %s."
            ) % process.company_id.name)
        if not account_conf.journal_dso_purchase_bbn_id:
            raise ValidationError(_(
                "Journal Pembelian BBN belum dikonfigurasi di Account Setting cabang %s."
            ) % process.company_id.name)
        return account_conf

    def _create_reverse_move(self, old_move, account_conf, process, from_biro_jasa, to_biro_jasa):
        """Buat jurnal balikan dari old_move (debit/credit dibalik).

        Args:
            old_move: account.move journal yang akan dibalik
            account_conf: account.setting record
            process: tw.vehicle.registration.process record
            from_biro_jasa: res.partner biro jasa yang dibalik
            to_biro_jasa: res.partner biro jasa tujuan (untuk keterangan ref)

        Returns:
            account.move: jurnal balikan yang sudah di-post
        """
        journal = account_conf.journal_dso_purchase_bbn_id
        prefix = process.company_id.code

        line_vals = self._prepare_reverse_lines(old_move, from_biro_jasa, process)
        move_vals = self._prepare_move_vals_cancel(journal, prefix, process, old_move.ref, from_biro_jasa, line_vals)
        move = self.env['account.move'].suspend_security().with_company(process.company_id).create(move_vals)
        move.suspend_security().action_post()
        return move

    def _create_new_move(self, old_move, account_conf, process, to_biro_jasa):
        """Buat jurnal Accrue BBN baru dengan to_biro_jasa sebagai partner.

        Args:
            old_move: account.move sebagai template nilai line
            account_conf: account.setting record
            process: tw.vehicle.registration.process record
            to_biro_jasa: res.partner biro jasa tujuan

        Returns:
            account.move: jurnal baru yang sudah di-post
        """
        journal = account_conf.journal_dso_purchase_bbn_id
        prefix = process.company_id.code

        line_vals = self._prepare_new_lines(old_move, to_biro_jasa, process)
        move_vals = self._prepare_move_vals_cancel(journal, prefix, process, old_move.ref, to_biro_jasa, line_vals)
        move = self.env['account.move'].suspend_security().with_company(process.company_id).create(move_vals)
        move.suspend_security().action_post()
        return move

    def _prepare_move_vals_cancel(self, journal, prefix, process, ref, partner, line_vals):
        """Siapkan dict nilai untuk pembuatan account.move.

        Args:
            journal: account.journal record
            prefix: str company code
            process: tw.vehicle.registration.process record
            ref: str keterangan referensi
            partner: res.partner biro jasa
            line_vals: list of (0, 0, dict)

        Returns:
            dict: nilai untuk create account.move
        """
        return {
            'move_type': 'entry',
            'journal_id': journal.id,
            'company_id': process.company_id.id,
            'division': process.division,
            'partner_id': partner.id,
            'date': fields.Date.today(),
            'ref': ref,
            'name': self.env['ir.sequence'].get_sequence_code(journal.code, prefix),
            'line_ids': line_vals,
        }

    def _prepare_reverse_lines(self, old_move, partner, process):
        """Balik posisi debit/credit setiap baris journal lama.

        Args:
            old_move: account.move yang akan dibalik
            partner: res.partner yang digunakan (biro jasa lama)
            process: tw.vehicle.registration.process record

        Returns:
            list of (0, 0, dict)
        """
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
                'company_id': process.company_id.id,
                'division': line.division or process.division,
            }))
        return line_vals

    def _prepare_new_lines(self, old_move, partner, process):
        """Salin posisi debit/credit dari journal lama dengan partner baru.

        Args:
            old_move: account.move sebagai template
            partner: res.partner biro jasa tujuan
            process: tw.vehicle.registration.process record

        Returns:
            list of (0, 0, dict)
        """
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
                'company_id': process.company_id.id,
                'division': line.division or process.division,
            }))
        return line_vals