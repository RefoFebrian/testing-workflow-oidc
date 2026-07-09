# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritAccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    # 7: defaults methods

    # 8: fields
    consolidated_qty = fields.Float(string='Consolidated Qty',help='Consolidated Quantity')
    division = fields.Selection(related='move_id.division', store=True, precompute=True)
    state = fields.Selection([('draft','Unbalanced'), ('valid','Balanced')], string='State', readonly=True, copy=False)
    is_receipt_printed = fields.Boolean('Cetak Kwitansi', default=False, help="Formerly known as 'kwitansi'")

    # 9: relation fields
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        compute='_compute_account_id', store=True, readonly=False, precompute=True,
        inverse='_inverse_account_id',
        index=False,  # covered by account_move_line_account_id_date_idx defined in init()
        auto_join=True,
        ondelete="cascade",
        domain="[('deprecated', '=', False), ('account_type', '!=', 'off_balance')]",
        check_company=False,
        tracking=True,
    )
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry',
        required=True,
        readonly=True,
        index=True,
        auto_join=True,
        ondelete="cascade",
        check_company=False,
    )
    company_id = fields.Many2one('res.company', string="Branch", required=True, related=False, index=True, precompute=False, readonly=False, default=lambda self: self.env.company)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _compute_account_id(self):
        super()._compute_account_id()
        # Mengubah Balancing Line (Partner Account) menjadi menggunakan default_debit/credit_account_id dari journalnya
        for line in self:
            if line.display_type == 'payment_term' and line.move_id.journal_id:
                move = line.move_id
                journal = move.journal_id
                target_account = False
                
                if move.is_sale_document(include_receipts=True) and journal.default_debit_account_id:
                    target_account = journal.default_debit_account_id
                elif move.is_purchase_document(include_receipts=True) and journal.default_credit_account_id:
                    target_account = journal.default_credit_account_id
                    
                if target_account:
                    if move.fiscal_position_id:
                        target_account = move.fiscal_position_id.map_account(target_account)
                    else:
                        target_account = target_account.with_company(move.company_id)
                    line.account_id = target_account.id

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('company_id'):
                if vals.get('move_id'):
                    move = self.env['account.move'].browse(vals['move_id'])
                    vals['company_id'] = move.company_id.id
                else:
                    vals['company_id'] = self.env.company.id
        created = super().create(vals_list)
        return created

    def unlink(self):
        for aml in self:
            if aml.move_id.state != 'draft':
                raise Warning('You cannot delete a document that is not in draft state')
        return super().unlink()

    # 13: action methods

    # 14: private methods

    def _check_reconciled(self):
        message = ''
        for line in self:   
            if line.reconciled:
                message += _("The line %s is already reconciled.\n") % line.name
            if not line.reconciled and line.matching_number:
                message += _("The line %s is already Partially reconciled.\n") % line.name
        if message:
            raise message
        return False
            
    