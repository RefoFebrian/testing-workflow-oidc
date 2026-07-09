# -*- coding: utf-8 -*-

# 1: imports of python lib
import json

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import AccessError
# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritAccountJournal(models.Model):
    _inherit = "account.journal"
    
    code = fields.Char(size=8)
    type = fields.Selection(selection_add=[('sale_refund', 'Sales Refund'), ('purchase_refund', 'Purchase Refund')], ondelete={"sale_refund": "set general", "purchase_refund": "set general"})
    partner_id = fields.Many2one('res.partner', string='Partner')
    company_id = fields.Many2one('res.company', string="Branch", required=True, readonly=False, index=True, default=lambda self: self.env.company.parent_id or self.env.company, help="Company related to this journal")
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency", default=lambda self: self.env.company.currency_id)
    default_credit_account_id = fields.Many2one(comodel_name='account.account', string='Default Credit Account')
    default_debit_account_id = fields.Many2one(comodel_name='account.account', string='Default Debit Account')

    @api.onchange('company_id')
    def _onchange_partner_bank_id(self):
        self.default_credit_account_id = False
        self.default_debit_account_id = False

    @api.onchange('partner_id')
    def _onchange_partner_bank_id(self):
        self.bank_account_id = False

    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_account.group_tw_account_journal_form_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
    
    @api.model
    def _alias_prepare_alias_name(self, alias_name, name, code, jtype, company):
        """ Tool method generating standard journal alias, to ensure uniqueness
        and readability;  reset for other journals than purchase / sale """
        if jtype not in ('purchase', 'sale'):
            return False

        alias_name = next(
            (
                string for string in (alias_name, name, code, jtype)
                if (string and self.env['mail.alias']._is_encodable(string) and
                    self.env['mail.alias']._sanitize_alias_name(string))
            ), False
        )
        if not company:
            alias_name = f"{alias_name}-main"
        elif company != self.env.ref('base.main_company'):
            company_identifier = self.env['mail.alias']._sanitize_alias_name(company.name) if self.env['mail.alias']._is_encodable(company.name) else company.id
            if f'-{company_identifier}' not in alias_name:
                alias_name = f"{alias_name}-{company_identifier}"
                
        return self.env['mail.alias']._sanitize_alias_name(alias_name)
    
    def _get_available_payment_method_lines(self, payment_type):
        payment_methods = super()._get_available_payment_method_lines(payment_type)
        if not self:
            return self.env['account.payment.method.line']
        self.ensure_one()
        if not payment_methods:
            if payment_type == 'inbound':
                account_payment_method_manual = self.env.ref('account.account_payment_method_manual_in')
            else:
                account_payment_method_manual = self.env.ref('account.account_payment_method_manual_out')
            payment_methods = self.env['account.payment.method.line'].sudo().create({
                'name': 'Manual',
                'payment_method_id': account_payment_method_manual.id,
                'journal_id': self.id,
                'payment_type': payment_type,
            })
            
        return payment_methods
        
    def _kanban_dashboard(self):
        dashboard_data = self._get_journal_dashboard_data_batched()
        for journal in self:
            # Ensure drag_drop_settings exists with default values for all journal types
            if 'drag_drop_settings' not in dashboard_data[journal.id]:
                dashboard_data[journal.id]['drag_drop_settings'] = {
                    'image': '',
                    'text': '',
                    'group': 'account.group_account_user',  # Default group if needed
                }
            journal.kanban_dashboard = json.dumps(dashboard_data[journal.id])
    
    @api.model
    def _fill_missing_values(self, vals, protected_codes=False):
        journal_type = vals.get('type')
        is_import = 'import_file' in self.env.context
        if is_import and not journal_type:
            vals['type'] = journal_type = 'general'

        # 'type' field is required.
        if not journal_type:
            return

        if journal_type in ('bank', 'cash'):
            has_liquidity_accounts = vals.get('default_account_id')
            if not has_liquidity_accounts:
                vals['default_account_id'] = vals.get('default_debit_account_id') or vals.get('default_credit_account_id')

        return super()._fill_missing_values(vals, protected_codes)
        