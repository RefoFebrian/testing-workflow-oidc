# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError, ValidationError, RedirectWarning

# 5: local imports

# 6: Import of unknown third party lib

class AccountAccountInherit(models.Model):
    _inherit = "account.account"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    company_ids = fields.Many2many('res.company', string="Branch", required=True, readonly=False, default=lambda self: self.env.company.parent_id or self.env.company)
    sap = fields.Char('SAP Code')
    is_can_be_collected = fields.Boolean('Allow Collecting?', help="Allow this account to be collected by branch.")
    sla = fields.Integer('SLA',help='Service Level Agreement of the occurance transaction in days.')
    parent_id = fields.Many2one('account.account', string='Parent')

    # 10: constraints & sql constraints
    @api.constrains('company_ids', 'account_type')
    def _check_company_consistency(self):
        if self.filtered(lambda a: a.account_type == 'asset_cash' and len(a.company_ids) > 1):
            raise ValidationError(_("Bank & Cash accounts cannot be shared between companies."))
        
        for companies, accounts in self.grouped(lambda a: a.company_ids).items():
            if self.env['account.move.line'].sudo().search_count([
                ('account_id', 'in', accounts.ids),
                '!',
                ('company_id', 'child_of', companies.ids)
            ], limit=1):
                raise UserError(_("You can't unlink this company from this account since there are some journal items linked to it."))

    # 11: compute/depends & on change methods

    # 12: override methods
    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_account.group_tw_account_account_form_read'):
            raise UserError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res
    
    # 13: action methods

    # 14: private methods