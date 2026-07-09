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

class TwBankTransferLinePust(models.Model):
    """Extends tw.bank.transfer.line to support PUST workflows.

    Adds PUST reference tracking, bank_types domain filter,
    and pilot-project-aware branch destination logic.

    Key behaviors:
    - Cash → Transit: shows transit journals (MN01xxx) as payment_to destination
    - Transit → Bank: shows bank journals as payment_to destination
    - Hides reimbursement field during transit flows
    - Prevents deletion of lines if parent BT is not in draft state
    """
    _inherit = "tw.bank.transfer.line"

    # 7: defaults methods

    # 8: fields
    pust_ref = fields.Char(string="Cash PUST Reference",store=True,readonly=True,copy=False,help="Name of the originating Cash-to-Transit PUST transfer.",)
    bank_types = fields.Char(string="Domain Bank Payment To",help="Used as dynamic domain filter for payment_to_id journal type.",)

    # 9: relation fields

    # 10: constraints & sql constraints
    
    # 11: compute/depends & onchange methods
    
    @api.onchange('branch_destination_id')
    def _onchange_branch_destination_pust(self):
        """Extend branch destination change for PUST flows.

        Replicates teds_pust TedsPUSTLine.branch_destination_change logic:
        1. Check pilot project:
           - No pilot → ALL branches use PUST.
           - Pilot exists → only registered branches.
        2. Cash → Transit: show transit journals (code = MN01 + destination code).
        3. Transit → Bank: show bank journals at destination branch.
        4. Hide reimbursement_id during transit operations.
        """
        pilot = self._is_pilot_pust()

        company_id = self.bank_transfer_id.company_id.id if self.bank_transfer_id else False

        if pilot is not None:
            # Pilot exists → check if current branch is registered
            pilot_company_ids = pilot.company_ids.ids
            if not company_id or company_id not in pilot_company_ids:
                return
            _logger.info('PILOT PROJECT %s is running', pilot.name)

        if not self.bank_transfer_id or not self.bank_transfer_id.journal_id:
            return

        bank_type = self.bank_transfer_id.journal_id.type
        if bank_type not in ('cash', 'transit'):
            return

        if not self.branch_destination_id:
            return

        dest_code = self.branch_destination_id.code if self.branch_destination_id else False

        domain = {
            'payment_to_id': [('id', '=', 0)],
            'reimbursement_id': [('state', '=', 'approved')],
        }

        if bank_type == 'cash':
            # Cash → Transit: show transit journals with code MN01 + destination code
            transit_code = 'MN01%s' % dest_code
            payment_to_ids = self.env['account.journal'].sudo().search([
                ('company_id.code', '=', dest_code),
                ('type', '=', 'transit'),
                ('code', '=', transit_code),
            ])
            if payment_to_ids:
                domain['payment_to_id'] = [('id', 'in', payment_to_ids.ids)]
                # Hide reimbursement when doing PUST transit
                domain['reimbursement_id'] = [('id', '=', 0)]

        elif bank_type == 'transit':
            # Transit → Bank: show bank journals at destination
            payment_to_ids = self.env['account.journal'].sudo().search([
                ('company_id.code', '=', dest_code),
                ('type', '=', 'bank'),
            ])
            if payment_to_ids:
                domain['payment_to_id'] = [('id', 'in', payment_to_ids.ids)]
                # Hide reimbursement when doing transit-to-bank
                domain['reimbursement_id'] = [('id', '=', 0)]

        self.payment_to_id = False
        return {'domain': domain}
 
    # 12: override methods    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to manage transit_ref synchronization.

        When a line with pust_ref is created (Transit-to-Bank flow),
        update the corresponding Cash-to-Transit PUST record's transit_ref
        with the parent bank transfer name.

        Replicates teds_pust TedsPUSTLine.create logic.
        """
        records = super().create(vals_list)

        for record in records:
            if record.bank_transfer_id.journal_id.type == 'transit':
                if not record.pust_ref:
                    raise Warning(
                        'PUST ref tidak boleh kosong untuk Bank type transit!'
                    )

                pust_record = self.env['tw.bank.transfer'].sudo().search([
                    ('name', '=', record.pust_ref),
                ], limit=1)
                if pust_record:
                    pust_record.write({
                        'transit_ref': record.bank_transfer_id.name,
                    })

        return records

    def unlink(self):
        """Override unlink to protect non-draft lines and clear transit_ref.

        Replicates teds_pust TedsPUSTLine.unlink logic:
        1. Prevent deletion if parent BT state is not 'draft'.
        2. Clear transit_ref on linked PUST record so it can be re-used.
        """
        for record in self:
            if record.bank_transfer_id.state != 'draft':
                raise Warning('Data selain draft tidak bisa dihapus!')

            if record.pust_ref:
                pust_record = self.env['tw.bank.transfer'].sudo().search([
                    ('name', '=', record.pust_ref),
                ], limit=1)
                if pust_record:
                    pust_record.write({'transit_ref': False})

        return super().unlink()
        
    # 13: action methods

    # 14: private methods
    def _is_pilot_pust(self):
        """Check if PUST pilot project is active.

        Returns:
        - None if no pilot project found (ALL branches use PUST)
        - tw.pilot.project recordset if pilot exists
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
            return None

        return pilot
