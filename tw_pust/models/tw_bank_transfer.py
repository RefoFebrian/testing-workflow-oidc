# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwBankTransferPust(models.Model):
    """Extends tw.bank.transfer to support PUST (Cash-in-Transit) workflows.

    PUST (Penerimaan Uang Setoran Tunai) manages the flow:
    - Cash → Transit: marks the BT as PUST (is_pust=True)
    - Transit → Bank: auto-populates lines from approved Cash-to-Transit records

    Integrates with Pilot Project to enable PUST only for designated branches.
    """
    _inherit = "tw.bank.transfer"

    # 7: defaults methods

    # 8: fields
    is_pust = fields.Boolean( string="PUST", store=True, copy=False, help="Indicates this is a PUST (Cash-in-Transit) transaction.")
    transit_ref = fields.Char( string="PUST Reference", store=True, copy=False, help="Name of the Transit-to-Bank transfer that consumed this PUST record.")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & onchange methods
    @api.onchange('journal_id')
    def _onchange_journal_pust(self):
        """Detect PUST scenario based on journal type.

        Replicates teds_pust.change_amount logic:
        - Requires company_id and division to be set.
        - Checks pilot project:
          - No pilot → ALL branches use PUST.
          - Pilot exists → only registered branches.
          - Pilot exists but branch not in list → skip (return False).
        - Cash journal: set is_pust = True.
        - Transit journal: auto-populate lines from approved PUST records.
        """
        if not self.journal_id:
            return

        pilot = self._is_pilot_pust()
        if pilot is False:
            # Pilot exists but current branch not in list → skip
            return

        if pilot is not None:
            # Pilot exists → check if current branch is registered
            pilot_company_ids = pilot.company_ids.ids
            if self.company_id.id not in pilot_company_ids:
                return
            _logger.info('PILOT PROJECT %s is running', pilot.name)

        # All required fields must be set (replicates teds: all([bank, branch_id, division]))
        if not all([self.journal_id, self.company_id, self.division]):
            return

        # Reset line_ids and is_pust before processing
        self.line_ids = [(5, 0, 0)]
        self.is_pust = False

        if self.journal_id.type == 'transit':
            # Transit → Bank: auto-populate from PUST Cash records
            self.amount = 0
            self._populate_pust_lines()

        elif self.journal_id.type == 'cash':
            # Cash → Transit: mark as PUST
            self.is_pust = True
    
    @api.onchange('division')
    def _onchange_division_pust(self):
        """Reset PUST-related fields when division changes.

        Replicates teds_pust.change_division logic:
        clears journal, is_pust flag, and line_ids.
        """
        self.journal_id = False
        self.is_pust = False
        self.line_ids = [(5, 0, 0)]


    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to detect and flag PUST transactions.
        """
        for vals in vals_list:
            if not vals.get('is_pust'):
                vals['is_pust'] = True
        return super().create(vals_list)

    # 13: action methods
    def action_confirm(self):
        """Override confirm to set is_pusted on cash journal.

        When a Cash-type Bank Transfer is posted, mark the journal as
        'pusted' (is_pusted=True). This is used by tw_payment to filter
        which journals are available for payment vouchers.

        Replicates wtc_bank_transfer.post_bank L204:
        self.payment_from_id.write({'is_pusted': True})
        """
        res = super().action_confirm()

        for record in self:
            if record.journal_id.type == 'cash':
                record.journal_id.write({'is_pusted': True})

        return res

    def action_cancel(self):
        super().action_cancel()
        for record in self:
            pust_record = self.env['tw.bank.transfer'].sudo().search([
                ('transit_ref', '=', record.name),
            ], limit=1)
            if pust_record:
                pust_record.write({'transit_ref': False})

    # 14: private methods
    def _populate_pust_lines(self):
        """Fetch approved Cash-to-Transit transfers and populate lines.

        Uses line-level lookup (replicates teds_pust._verify_transit_pust):
        - Searches for PUST lines with payment_to_id code 'MN01' + branch_code
        - Populates the current BT with those line details
        - Sets bank_types = 'bank' so payment_to_id domain filters to bank journals
        """
        try:
            transit_pust_list = self._verify_transit_pust(
                self.company_id.id,
                self.company_id.name,
                self.company_id.code,
                self.division,
            )
        except Warning:
            # No PUST records found — just return silently during onchange
            return

        if not transit_pust_list:
            return

        lines = []
        total_amount = 0.0
        for transit in transit_pust_list:
            total_amount += transit.amount
            lines.append((0, 0, {
                'bank_types': 'bank',
                'branch_destination_id': transit.branch_destination_id.id,
                'description': transit.description,
                'amount': transit.amount,
                'pust_ref': transit.bank_transfer_id.name,
            }))

        self.amount = total_amount
        self.line_ids = lines

    def _is_pilot_pust(self):
        """Check if PUST pilot project is active and return the pilot record.

        Searches tw.pilot.project for an active record whose model_id
        points to tw.bank.transfer. This is the model used by PUST.

        Returns:
        - None if no pilot project found (meaning ALL branches use PUST)
        - tw.pilot.project recordset if pilot exists (only listed branches)
        - False if pilot exists but current branch is NOT in the list
        """
        bt_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'tw.bank.transfer')], limit=1
        )
        if not bt_model:
            return None

        pilot = self.env['tw.pilot.project'].sudo().search([
            ('model_id', '=', bt_model.id),
            ('active', '=', True),
        ], limit=1)

        if not pilot:
            # No pilot project → ALL branches use PUST
            return None

        return pilot

    def _get_pust_posted_states(self):
        """Return the list of states considered 'confirmed' for PUST filter.

        If tw_bank_transfer_approval module is installed, Cash PUST records
        can be in either 'approved' or 'posted' state (both are valid).
        Otherwise, only 'posted' is the confirmed state.

        :return: list of state strings
        """
        approval_module = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'tw_bank_transfer_approval'),
            ('state', '=', 'installed'),
        ], limit=1)
        if approval_module:
            return ['approved', 'posted']
        return ['posted']

    def _verify_transit_pust(self, company_id, company_name, company_code, division):
        """Search for approved Cash-to-Transit PUST lines targeted at this branch.

        Logic replicates teds_pust._verify_transit_pust:
        1. Find header records: Cash BTs that are approved/posted, is_pust=True,
           not yet consumed (transit_ref=False), same branch & division.
        2. Find line records: lines whose payment_to_id code = 'MN01' + branch_code.

        :param company_id: int, the company/branch id
        :param company_name: str, the company/branch name
        :param company_code: str, the company/branch code
        :param division: str, the division value
        :return: tw.bank.transfer.line recordset
        :raises Warning: if no transit PUST found
        """
        posted_states = self._get_pust_posted_states()
        pust_ids = self.search([
            ('journal_id.type', '=', 'cash'),
            ('state', 'in', posted_states),
            ('company_id', '=', company_id),
            ('is_pust', '=', True),
            ('transit_ref', '=', False),
            ('division', '=', division),
        ])

        transit_code = 'MN01%s' % company_code
        pust_lines = self.env['tw.bank.transfer.line'].sudo().search([
            ('bank_transfer_id', 'in', pust_ids.ids),
            ('payment_to_id.code', '=', transit_code),
        ])

        if not pust_lines:
            raise Warning(
                'Daftar transaksi transit untuk cabang %s tidak ditemukan!' % company_name
            )
        return pust_lines