# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwCollectingExpedition(models.Model):
    """Model for expedition collecting with stock inbound support.
    
    Inherits from tw.collecting for base collecting functionality
    and tw.approval.mixin for approval workflow.
    """

    _name = "tw.collecting.expedition"
    _description = "Collecting Expedition"
    _inherit = ["tw.collecting", "tw.approval.mixin"]
    _order = "id desc"

    # 7: defaults methods

    # 8: fields
    is_correction = fields.Boolean(
        string='Is Correction',
        default=False,
        help='Indicates if this is a correction entry'
    )
    estimated_amount = fields.Monetary(
        string='Estimated Amount',
        currency_field='currency_id',
        default=0.0,
        readonly=True,
        help='Estimated amount from journal accrue calculation'
    )
    difference_amount = fields.Monetary(
        string='Difference',
        currency_field='currency_id',
        compute='_compute_difference_amount',
        store=True,
        help='Difference between amount and estimated (amount - estimated)'
    )

    # 9: relation fields
    move_line_ids = fields.Many2many(
        'account.move.line',
        'tw_collecting_expedition_move_line_rel',
        'collecting_id',
        'move_line_id',
        string='Journal Items',
        copy=False
    )
    stock_inbound_ids = fields.Many2many(
        comodel_name='tw.stock.inbound',
        relation='tw_collecting_expedition_stock_inbound_rel',
        column1='collecting_id',
        column2='stock_inbound_id',
        string='Stock Inbounds',
        help='Related stock inbound for expedition collecting'
    )
    line_ids = fields.One2many(
        comodel_name='tw.collecting.expedition.line',
        inverse_name='collecting_expedition_id',
        string='Detail Lines',
        copy=False,
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('amount', 'estimated_amount')
    def _compute_difference_amount(self):
        """Compute difference between amount and estimated."""
        for record in self:
            record.difference_amount = record.amount - record.estimated_amount

    @api.onchange('partner_id')
    def _onchange_partner_id_clear_inbound(self):
        """Clear stock_inbound_ids when partner changes."""
        self.stock_inbound_ids = [(5, 0, 0)]

    @api.onchange('division')
    def _onchange_division_clear_inbound(self):
        """Clear stock_inbound_ids when division changes."""
        self.stock_inbound_ids = [(5, 0, 0)]

    @api.onchange('date_start', 'date_end')
    def _onchange_date_filter_clear_inbound(self):
        """Clear stock_inbound_ids when date filter changes."""
        self.stock_inbound_ids = [(5, 0, 0)]

    @api.onchange('stock_inbound_ids')
    def _onchange_stock_inbound_ids(self):
        """Auto-populate partner, move_line_ids, and line_ids from stock inbound.

        - Sets partner from first inbound's expedition.
        - Collects credit lines from all accrue journal entries.
        - Builds detail lines per stock.move.line with picking, product,
          lot (no mesin), chassis_number (no rangka, if unit), and qty.
        """
        if self.stock_inbound_ids:
            # Set partner from first inbound expedition
            if not self.partner_id:
                first_inbound = self.stock_inbound_ids[0]
                if first_inbound.expedition_id:
                    self.partner_id = first_inbound.expedition_id.id

            # Populate move_line_ids with credit lines from inbound journal entries
            credit_lines = self.env['account.move.line']
            for inbound in self.stock_inbound_ids:
                if inbound.move_ids:
                    credit_lines |= inbound.move_ids.line_ids.filtered(
                        lambda line: line.credit > 0
                    )
            self.move_line_ids = credit_lines

            # Calculate total amount from credit lines
            total_amount = sum(credit_lines.mapped('credit'))
            self.amount = total_amount
            self.estimated_amount = total_amount

            # Build detail lines from stock move lines per picking
            line_vals = self._build_expedition_line_vals()
            self.line_ids = [(5, 0, 0)] + [(0, 0, v) for v in line_vals]
        else:
            self.move_line_ids = [(5, 0, 0)]
            self.line_ids = [(5, 0, 0)]
            self.amount = 0.0
            self.estimated_amount = 0.0

    # 12: override methods
    def _create_account_move(self):
        """Override to create collecting entry with billing amount.
        
        Credit line uses self.amount (billing) instead of sum of move_line_ids (estimated).
        Difference line is created to balance the entry.
        """
        self.ensure_one()
        
        # Validate journal config exists
        branch_setting = self.company_id.branch_setting_id
        if not branch_setting or not branch_setting.account_setting_id:
            raise UserError(_("Account Setting belum dikonfigurasi pada Branch Setting."))
            
        journal_obj = branch_setting.account_setting_id.get_account_setting(
            'journal_collecting_expedition_id'
        )
        if not journal_obj:
            raise UserError(_(
                "Journal Collecting Expedition belum dikonfigurasi. "
                "Silakan setting di Account Setting terlebih dahulu."
            ))
        
        # Set account from journal config
        self.account_id = journal_obj.default_credit_account_id
        if not self.account_id:
            raise UserError(_(f"Default Credit Account belum dikonfigurasi di Journal Collecting Expedition {journal_obj.name}."))
        
        today = self._get_default_date()
        period_id = self.env['tw.account.period']._get_current_periods(today).id
        journal_id = journal_obj.id
        
        move_line_vals = []
        warning = ""
        
        # Get stock valuation account from accrue entries debit lines
        debit_account = None
        for inbound in self.stock_inbound_ids:
            if inbound.move_ids:
                for move in inbound.move_ids:
                    debit_lines = move.line_ids.filtered(
                        lambda line: line.debit > 0
                    )
                    if debit_lines:
                        debit_account = debit_lines[0].account_id
                        break
                if debit_account:
                    break
        
        # Validate debit_account if difference exists
        if self.difference_amount and not debit_account:
            raise UserError(_("Tidak dapat menemukan akun debit dari Journal accrue. Pastikan Stock Inbound memiliki journal entry dengan debit line."))
        
        # Create reverse lines from move_line_ids (accrue entries)
        for move_line in self.move_line_ids:
            if move_line.reconciled:
                warning += "- %s \r\n" % move_line.name
            
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
        
        if warning:
            from odoo.exceptions import Warning
            raise Warning(
                "Transaksi berikut sudah di reconcile (sebagian / penuh):\r\n %s " % warning
            )
        
        # Create collecting line with BILLING AMOUNT (self.amount), not estimated
        move_line_vals.append({
            'company_id': self.company_id.id,
            'debit': 0,
            'credit': self.amount,  # Use billing amount
            'name': self.description,
            'ref': self.name,
            'account_id': self.account_id.id,
            'partner_id': self.partner_id.id,
            'division': self.division,
            'date_maturity': self.date_maturity if self.date_maturity else today,
        })
        
        # Add difference line if there's difference and we have debit account
        if self.difference_amount:
            difference = abs(self.difference_amount)
            is_positive = self.difference_amount > 0
            
            move_line_vals.append({
                'company_id': self.company_id.id,
                'debit': difference if is_positive else 0.0,
                'credit': difference if not is_positive else 0.0,
                'name': f'Difference Expedition - {self.name}',
                'ref': self.name,
                'account_id': debit_account.id,
                'partner_id': self.partner_id.id,
                'division': self.division,
                'date_maturity': today,
            })

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
        
        # Reconcile lines - only lines with same account as move_line_ids
        # Exclude difference line (different account: stock valuation)
        accounts_to_reconcile = self.move_line_ids.mapped('account_id')
        to_reconcile_ids = move_id.line_ids.filtered(
            lambda x: x.name != x.move_id.name and x.account_id in accounts_to_reconcile
        )
        to_reconcile_ids += self.move_line_ids
        to_reconcile_ids.sudo().reconcile()
        
        return move_id

    # 13: action methods
    def action_view_journal_entry(self):
        """Open the journal entry related to this collecting."""
        self.ensure_one()
        if not self.collected_move_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.collected_move_id.id,
            'target': 'current',
        }

    # 14: private methods
    def _build_expedition_line_vals(self):
        line_vals = []
        inbound_ids = self.stock_inbound_ids.ids
        if not inbound_ids:
            return line_vals

        picking_obj = self.env['stock.picking'].suspend_security().search([
            ('stock_inbound_id', 'in', inbound_ids),
            ('state', '=', 'done'),
        ])

        for picking in picking_obj:
            for move in picking.move_ids_without_package:
                for ml in move.move_line_ids:
                    vals = {
                        'picking_id': picking.id,
                        'product_id': ml.product_id.id,
                        'lot_id': ml.lot_id.id if ml.lot_id else False,
                        'chassis_number': ml.lot_id.chassis_number if ml.lot_id else False,
                        'qty': ml.quantity,
                    }
                    line_vals.append(vals)
        return line_vals


