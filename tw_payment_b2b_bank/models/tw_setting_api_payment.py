# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class SettingApiPayment(models.Model):
    _name = "tw.setting.api.payment"
    _description = 'API Payment Setting'

    # 7: defaults methods

    # 8: fields
    channel_id = fields.Char(string='Channel ID', help='Given by Bank or Fintech service provider')
    merchant_id = fields.Char(string='Merchant ID', help='Given by Bank or Fintech service provider (Credential ID)')
    terminal_id = fields.Char(string='Terminal ID', help='Given by Bank or Fintech service provider')
    x_partner_id = fields.Char(string='X Partner ID', help='Given by Bank or Fintech service provider')
    x_partner_id_notify = fields.Char(string='X Partner ID Notify', help='Given by Bank or Fintech service provider')
    service_code = fields.Char(string='Service Code', help='Given by Bank or Fintech service provider')
    sub_company = fields.Char(string='Sub Company', help='Given by Bank or Fintech service provider')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), string='Division', help='Kebutuhan untuk API Payment, ex: QRIS dan VA')
    payment_usage = fields.Selection(string='Payment Usage', selection=lambda self: self.env['tw.selection'].get_option_list('PaymentUsage'), default='qris')

    # 9: relation fields
    payment_provider_id = fields.Many2one(comodel_name='payment.provider', string='Setting', ondelete='cascade')
    provider_id = fields.Many2one(comodel_name='res.partner', string='Provider', domain=['|', ('is_bank','=',True), ('is_fintech','=',True)])

    # 10: constraints & sql constraints
    _sql_constraints = [('api_payment_setting_unique', 'unique(division, payment_usage, provider_id)', 'Data API Payment Setting tidak boleh duplikat !')]

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods