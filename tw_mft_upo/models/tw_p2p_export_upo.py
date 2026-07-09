# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import math

# 2: import of known third party lib
import xlrd
import base64

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwP2pExportUpo(models.Model):
    _name = "tw.p2p.export.upo"
    _description = "P2P Export UPO"

    # 7: defaults methods
    def _get_default_main_dealer_atpm_code(self):
        return self.env['res.company'].get_default_main_dealer_atpm_code()
    
    # 8: fields
    filename = fields.Char(string='Filename', readonly=True)
    state = fields.Selection([
        ('open','Open'),
        ('done','Done'),
        ('revision','Revision'),
        ('closed','Closed'),
    ], default='open',string='Status')
    content = fields.Text(string='Content', readonly=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, readonly=True)
    
    # Audit Trail
    
    # 9: relation fields
    purchase_order_id = fields.Many2one('tw.p2p.purchase.order', string='Purchase Order')

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods

    # 13: action methods
    def action_revision(self):
        self.write({
            'state': 'revision'
        })

    def action_done(self):
        self.write({
            'state': 'done'
        })
    
    def action_closed(self):
        self.write({
            'state': 'closed'
        })

    # 14: private methods

