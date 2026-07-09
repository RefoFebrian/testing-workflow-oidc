from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class InheritResPartner(models.Model):
    _inherit = "res.partner"
    # INFO : Override from Partner and Connected to Sale Order

    credit_limit_unit = fields.Float(string='Credit Limit Unit', digits='Product Price')
    credit_limit_sparepart = fields.Float(string='Credit Limit Sparepart', digits='Product Price')