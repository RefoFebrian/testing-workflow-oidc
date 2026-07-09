# -*- coding: utf-8 -*-

# 1: imports of python lib
import qrcode
import base64
import io
from datetime import date, datetime, timedelta,time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWQRCodeUnit(models.Model):
    _name = "tw.qr.code.unit"
    _description = "QR Code For all Unit"
    _order = 'create_date desc'
    
    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now()

    # 8: fields
    name = fields.Char('Kode Unik')
    qr_code_base64 = fields.Text(string="QR Code (Base64)")
    date = fields.Date('Date', default=_get_default_date)
    state = fields.Selection([
        ('New', 'New'),
        ('Printed', 'Printed'),
        ('Linked', 'Linked')
    ], string='Status', default='New')

    # Audit Trail
    printed_date = fields.Datetime('Pinted on')
    printed_uid = fields.Many2one('res.users', string='Printed by')
    
    # 9: relation fields
    lot_id = fields.Many2one('stock.lot', string='Serial Number')
    company_id = fields.Many2one('res.company', string='Branch', default=lambda self: self.env.company)

    # 10: constraints & sql constraints
    _sql_constraints = [('name_unique', 'unique(name)', 'The Name must be unique!')]

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_generate_qr_code(self):
        form_id = self.env.ref('tw_qr_code_unit.tw_generate_qr_code_unit_wizard_view').id
        
        return {
            'name': 'Generate QR Code',
            'res_model': 'tw.generate.qr.code.unit.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(form_id, 'form')],
            'target': 'new'
        }

    # 14: private methods
    def _check_qr_code(self, qr_code, company_id=False):
        if qr_code:
            qr_code_unit = self.suspend_security().search([
                ('name', '=', qr_code),
                ('company_id', '=', company_id or self.env.company.id),
                ('state', '=', 'Printed')
            ], limit=1)
            if not qr_code_unit:
                raise Warning(f"QR Code '{qr_code}' Not Found / Already Linked!")
    
