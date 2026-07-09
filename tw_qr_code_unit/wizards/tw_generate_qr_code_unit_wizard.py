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
import string
import random
# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWGenerateQRCodeUnitWizard(models.TransientModel):
    _name = "tw.generate.qr.code.unit.wizard"
    _description = "Generate QR Code Unit Wizard"
    
    # 7: defaults methods

    # 8: fields
    qty = fields.Integer('Qty', default=1)

    # Audit Trail
    
    # 9: relation fields
    company_id = fields.Many2one('res.company', string='Branch')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def get_unique_code(self, length):
        characters = string.ascii_letters + string.digits
        unique_code = ''.join(random.choice(characters) for qr in range(length))
        return unique_code
    
    def generate_unique_code_with_check(self, existing_codes, length):
        while True:
            code = self.get_unique_code(length)
            if code not in existing_codes:
                return code

    # 13: action methods
    def action_generate_qr_code_unit(self):
        try:
            if self.qty <= 0:
                raise Warning('Quantity must be greater than 0!')

            qr_code_ids = []
            existing_codes = list(set(self.env['tw.qr.code.unit'].search([]).mapped('name')))
            for qr in range(self.qty):
                get_unique_code = self.get_unique_code(12)
                
                qr_code_obj = self.env['tw.qr.code.unit'].sudo().search([
                    ('name','=',get_unique_code)
                ])
                if not qr_code_obj:
                    existing_codes.append(get_unique_code)
                    qr_code_obj = self.env['tw.qr.code.unit'].sudo().create({
                        'name':get_unique_code,
                        'company_id':self.company_id.id,
                        'state':'New'
                    })
                    qr_code_ids.append(qr_code_obj.id)
                else:
                    get_unique_code = self.generate_unique_code_with_check(existing_codes,12)
                    qr_code_obj = self.env['tw.qr.code.unit'].sudo().create({
                        'name':get_unique_code,
                        'company_id':self.company_id.id,
                        'state':'New'
                    })
                    qr_code_ids.append(qr_code_obj.id)
            return self.action_view_generate_qr_code_unit(qr_code_ids)
                    
        except Exception as err:
            raise Warning(f"Failed to generate qr code unit because : '{str(err)}'")
            

    # 14: private methods
    def action_view_generate_qr_code_unit(self, qr_code_ids):
        list_id = self.env.ref('tw_qr_code_unit.tw_qr_code_unit_list_view').id
        return {
            'name': 'QR Code Unit',
            'res_model': 'tw.qr.code.unit',
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'domain': [('id', 'in', qr_code_ids)],
            'view_id': list_id
        }
    
