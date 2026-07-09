# Copyright (C) 2025 Tunas Group
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class TwAccountFilter(models.Model):
    """Account Filter Model.
    
    This model provides account filtering functionality based on various criteria
    such as account type, prefix, and user type.
    """
    _name = "tw.account.filter"
    _description = "Account Filter"

    name = fields.Char(string='Reference/Description', related='transaction_type_id.name')
    code = fields.Char(string='Code', compute='_compute_code', store=True, index=True)
    
    # Filter by prefix / internal group / account type
    prefix = fields.Char(string='Prefix', help='Account code prefix for filtering.')
    internal_group = fields.Selection(
        selection=[
            ('equity', 'Equity'),
            ('asset', 'Asset'),
            ('liability', 'Liability'),
            ('income', 'Income'),
            ('expense', 'Expense'),
            ('off', 'Off Balance'),
        ],
        string="Internal Type"
    )
    account_type = fields.Selection(
        selection=[
            ("asset_receivable", "Receivable"),
            ("asset_cash", "Bank and Cash"),
            ("asset_current", "Current Assets"),
            ("asset_non_current", "Non-current Assets"),
            ("asset_prepayments", "Prepayments"),
            ("asset_fixed", "Fixed Assets"),
            ("liability_payable", "Payable"),
            ("liability_credit_card", "Credit Card"),
            ("liability_current", "Current Liabilities"),
            ("liability_non_current", "Non-current Liabilities"),
            ("equity", "Equity"),
            ("equity_unaffected", "Current Year Earnings"),
            ("income", "Income"),
            ("income_other", "Other Income"),
            ("expense", "Expenses"),
            ("expense_depreciation", "Depreciation"),
            ("expense_direct_cost", "Cost of Revenue"),
            ("off_balance", "Off-Balance Sheet"),
        ],
        string="Account Type"
    )
    
    # Relation Field
    transaction_type_id = fields.Many2one('tw.selection', string='Transaction Type', domain=[('type', '=', 'AccountFilterTransactionType')]) 
    
    
    @api.depends('transaction_type_id')
    def _compute_code(self):
        for record in self:
            record.code = record.transaction_type_id.value if record.transaction_type_id else ''
    
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('prefix') and not vals.get('internal_group') and not vals.get('account_type'):
                raise UserError(_("Please fill at least one Filter."))
            
        result = super().create(vals_list)
        return result
    
    def write(self, vals):
        write = super().write(vals)
        if not self.prefix and not self.internal_group and not self.account_type:
            raise UserError(_("Please fill at least one Filter."))
        return write
    
    
    def get_account_domain(self, code):
        """Generate a domain filter for accounts based on the filter criteria.
        
        Args:
            code (str): The code of the filter to apply.
            
        Returns:
            list: A domain filter list that can be used in search() or domain.
        """
        if not isinstance(code, str):
            raise UserError(_("Filter code must be a string."))
            
        domain = []
        account_filters = self.search([('code', '=', code)])
        
        if not account_filters:
            return domain
            
        # If multiple filters, combine them with OR conditions
        if len(account_filters) > 1:
            domain = ['|'] * (len(account_filters) - 1)
            
        for filter in account_filters:
            filter_domain = []
            
            # Build filter conditions
            conditions = []
            if filter.internal_group:
                conditions.append(('internal_group', '=', filter.internal_group))
            if filter.account_type:
                conditions.append(('account_type', '=', filter.account_type))
            if filter.prefix:
                conditions.append(('code', '=ilike', f"{filter.prefix}%"))
                
            # Combine conditions with AND
            if conditions:
                for cond in conditions[1:]:
                    filter_domain.append('&')
                filter_domain.extend(conditions)
                
            domain.extend(filter_domain)
        return domain
