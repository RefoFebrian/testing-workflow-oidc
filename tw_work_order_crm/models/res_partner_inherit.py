# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class ResPartner(models.Model):
    _inherit = "res.partner"

    # 7: defaults methods

    # 8: fields

    consumer_age = fields.Selection([
        ('<25', '<25'),
        ('26-35', '26-35'),
        ('36-50', '36-50'),
        ('>50', '>50')
    ], string="Usia Konsumen")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('identification_number')
    def onchange_ktp(self):
        if self.identification_number:
            if not self.identification_number.isdigit() or len(self.identification_number) != 16:
                warning = {'title':'Perhatian !','message':'No KTP harus 16 digit dan angka !'}
                self.identification_number = False
                return {'warning':warning}

    @api.onchange('mobile')
    def mobile_wo_onchange(self):
        if self.mobile :
            # Because mobile now contains symbol i.e. +, - we have to clean it first before checking
            cleaned_mobile = ''.join(filter(str.isdigit, self.mobile))            
            if len(cleaned_mobile) < 6 :
                raise Warning('Mobile Tidak boleh kurang dari 6 digit !.')
            else :
                cek = cleaned_mobile.isdigit()
            if not cek :
                raise Warning('Mobile hanya boleh angka !')
        return {'mobile' : {'mobile':self.mobile} }

    # 12: override methods