# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwKategoriNilaiMesin(models.Model):
    _name = "tw.kpb.engine.type"
    _description = "TW KPB Engine Type"

    # 7: defaults methods

    # 8: fields
    engine_no = fields.Char('Engine Number')
    name = fields.Char('Kategori')

    # 9: relation fields
    kategori_line = fields.One2many('tw.kpb.engine.price', 'kategori_id', string='Kategori Nilai Mesin')

    # 10: constraints & sql constraints
    @api.constrains('name', 'engine_no')
    def _check_unique_name_engine_no(self):
        for rec in self:
            if self.search([
                ('name', '=', rec.name),
                ('engine_no', '=', rec.engine_no),
                ('id', '!=', rec.id)  # Hindari memeriksa diri sendiri
            ]):
                raise ValidationError(_("Nomor Engine dan Nama Kategori harus unik!"))

    # 11: compute/depends & on change methods

    # 12: override methods    

class TwKategoriNilaiMesinLine(models.Model):
    _name = "tw.kpb.engine.price"
    _rec_name = "kpb_ke"
    _description = "TW KPB Engine Price"
    _order = 'kpb_ke ASC'
    
    # 7: defaults methods

    # 8: fields
    kpb_ke = fields.Integer('KPB Ke')
    jasa = fields.Float('Jasa')
    oli = fields.Float('Oli')

    # 9: relation fields
    kategori_id = fields.Many2one('tw.kpb.engine.type', string="Kategori Nilai Mesin")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods