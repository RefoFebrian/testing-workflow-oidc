# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class ResPartnerBankInherit(models.Model):
    _inherit = "res.partner.bank"

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    plafon = fields.Float(string='Plafon')
    float_amount = fields.Float(string='Float Amount')
    hold_amount = fields.Float(string='Hold Amount')
    available_balance = fields.Float(string='Available Balance')
    balance = fields.Float(string='Balance')
    is_fetch_statement = fields.Boolean(string='Fetch Statement')
    last_balance_check = fields.Datetime(string='Last Balance Check', default=_get_default_date)
    last_fetch = fields.Datetime(string='Last Fetch', default=_get_default_date)

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', domain=[('parent_id','!=',False)])
    api_config_id = fields.Many2one(comodel_name='tw.api.configuration', string='API Configuration', domain=[('api_type_id.value','in',('bca', 'bri', 'bni', 'mandiri'))])
    schedule_id = fields.Many2one(comodel_name='tw.api.schedule', string='Schedule')
    account_id = fields.Many2one(comodel_name='account.account', string='Account')

    # 10: constraints & sql constraints
    _sql_constraints = [('acc_number_unique', 'unique(acc_number)', 'Account Number tidak boleh duplikat !')]

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super(ResPartnerBankInherit, self).create(vals_list)

        return create
    
    def write(self, vals):
        write = super(ResPartnerBankInherit, self).write(vals)

        return write

    # 13: action methods
    def action_partner_bank_b2b_bank_tree(self):
        domain = [('api_config_id','!=',False)]
        name = 'Bank Accounts'
        path = 'bank-accounts'
        list_view_id = self.env.ref('base.view_partner_bank_tree').id
        form_view_id = self.env.ref('tw_b2b_bank.res_partner_bank_b2b_bank_form_view').id
        search_view_id = self.env.ref('base.view_partner_bank_search').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'res.partner.bank',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }

    # 14: private methods