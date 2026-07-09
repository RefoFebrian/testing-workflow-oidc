# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwGoodReceiveCancel(models.Model):
    """
    Model untuk membatalkan Good Receive (GR) dengan approval workflow.
    
    Flow:
    1. User create cancel request, pilih GR yang akan dibatalkan
    2. Request approval
    3. Setelah approved, confirm untuk:
       - Validasi tidak ada akuisisi terkait
       - Reverse JGR (Journal Good Receive)
       - Stock return
       - Set GR state ke cancel
    """
    _name = "tw.good.receive.cancel"
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = 'Good Receive Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()

    # 8: fields
    
    # 9: relation fields
    good_receive_id = fields.Many2one(
        'tw.good.receive', 
        string='Good Receive',
        domain="[('state', 'in', ['open', 'done']), ('company_id', '=', company_id)]",
        required=True,
        readonly=True,
    )
    cancellation_id = fields.Many2one(
        'tw.cancellation', 
        required=True, 
        ondelete='cascade'
    )

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('unique_good_receive_id', 'unique(good_receive_id)', 
         'Good Receive ini sudah pernah diinput untuk pembatalan sebelumnya!')
    ]

    # 11: compute/depends & on change methods
    @api.onchange('good_receive_id')
    def _onchange_good_receive_id(self):
        if self.good_receive_id:
            self.transaction_name = self.good_receive_id.name
        else:
            self.transaction_name = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('good_receive_id'):
                gr = self.env['tw.good.receive'].browse(vals['good_receive_id'])
                vals['transaction_name'] = gr.name
                name = "X" + gr.name
                self._check_duplicate_transaction(name)
                vals['name'] = name
                vals['date'] = self._get_default_date()
        return super(TwGoodReceiveCancel, self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise UserError('Warning! \nTidak bisa menghapus record selain status draft!')
        return super(TwGoodReceiveCancel, self).unlink()

    # 13: action methods
    def action_request_approval(self):
        """Request approval untuk cancel GR"""
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.state}')
        return super().action_request_approval(value=5)

    def action_confirm(self):
        """
        Confirm cancellation setelah approved.
        1. Check acquisition dependency
        2. Reverse JGR journal
        3. Stock return (commented for future)
        4. Set GR to cancel state
        """
        self.ensure_one()
        
        if not self.good_receive_id:
            raise Warning("Good Receive belum dipilih!")

        # 1. Check if any line has been acquired
        self._check_acquisition_dependency()

        # 2. Cancel pending pickings (for future)
        # self._picking_cancel()

        # 3. Stock return (for future)
        # self._return_picking()

        # 4. Reverse JGR journal
        self._reverse_gr_journal()

        # 5. Set GR to cancel state
        self.good_receive_id.write({
            'state': 'cancel',
            'cancel_uid': self.env.uid,
            'cancel_date': fields.Datetime.now(),
        })

        # 6. Update cancellation record
        return self.cancellation_id.action_confirm()

    # 14: private methods
    def _check_duplicate_transaction(self, name):
        """Delegate to parent cancellation model"""
        return self.cancellation_id._check_duplicate_transaction(name)

    def _check_acquisition_dependency(self):
        """
        Check if any GR line has been acquired.
        If yes, raise warning to cancel acquisition first.
        """
        acquired_lines = self.good_receive_id.move_asset_ids.filtered(
            lambda l: l.qty_acquired > 0
        )
        
        if acquired_lines:
            # Find related acquisitions
            acquisitions = self.env['tw.asset.acquisition'].search([
                ('good_receive_id', '=', self.good_receive_id.id),
                ('state', '!=', 'cancel')
            ])
            
            acq_names = ', '.join(acquisitions.mapped('name')) if acquisitions else 'N/A'
            
            raise Warning(_(
                "Good Receive ini memiliki GR Line yang sudah di-akuisisi!\n\n"
                "GR Lines yang sudah acquired:\n%s\n\n"
                "Akuisisi terkait: %s\n\n"
                "Silakan batalkan Akuisisi terlebih dahulu sebelum membatalkan Good Receive."
            ) % (
                '\n'.join([f"- {l.product_id.name} (Acquired: {l.qty_acquired})" for l in acquired_lines]),
                acq_names
            ))

    def _reverse_gr_journal(self):
        """
        Reverse Journal Good Receive (JGR).
        Creates a reversal entry for the GR journal.
        """
        if not self.good_receive_id.move_id:
            return  # No journal to reverse

        branch_config = self.company_id.branch_setting_id.account_setting_id
        if not branch_config:
            raise Warning("Branch Config tidak ditemukan!")

        journal_cancel_id = branch_config.journal_good_receive_cancel_id
        if not journal_cancel_id:
            raise Warning(
                "Journal Good Receive Cancel belum diisi di Branch Config!\n"
                "Silakan setting di menu: Accounting > Configuration > Account Setting"
            )

        # Create reversal
        move_reversal = self.env['account.move.reversal'].sudo().with_context(
            active_model='account.move',
            active_ids=self.good_receive_id.move_id.ids
        ).create({
            'date': datetime.now(),
            'journal_id': journal_cancel_id.id,
        })
        
        reversal = move_reversal.sudo().reverse_moves()
        if reversal:
            self.move_id = reversal.get('res_id', False)
            # Post the reversal
            if self.move_id:
                self.env['account.move'].browse(self.move_id).action_post()

    def _picking_cancel(self):
        """
        Cancel any pending pickings related to GR.
        (For future use)
        """
        # TODO: Implement when needed
        # picking_ids = self.good_receive_id.filtered(lambda p: p.state != 'done')
        # for picking in picking_ids:
        #     picking.action_cancel()
        pass

    def _return_picking(self):
        """
        Create stock return for completed pickings.
        (For future use)
        """
        # TODO: Implement when needed
        # This would create return pickings for any goods that were received
        pass

    def _prepare_return_picking(self, picking_ids):
        """
        Prepare return picking values.
        (For future use)
        """
        vals_list = []
        for picking in picking_ids:
            line_return_moves = []
            for move in picking.move_ids:
                line_return_moves.append((0, 0, {
                    'product_id': move.product_id.id,
                    'move_id': move.id,
                    'quantity': move.quantity,
                }))
            vals_list.append({
                'picking_id': picking.id,
                'product_return_moves': line_return_moves
            })
        return vals_list
