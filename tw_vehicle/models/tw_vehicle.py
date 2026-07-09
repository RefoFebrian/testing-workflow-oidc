# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWVehicle(models.Model):
    _name = "tw.vehicle"
    _description = "Vehicle for Expedisi"
    _rec_name = 'plate_number'
    
    # 7: defaults methods

    # 8: fields
    plate_number = fields.Char(string='Plat Number')

    # 9: relation fields
    partner_id = fields.Many2one('res.partner', string="Expedition", domain=[('category_id.name','=','Expedition')])

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('unique_plate_number', 'unique(plate_number,partner_id)', 'Master sudah ada !'),
    ]

    # 11: compute/depends & on change methods
    @api.onchange('plate_number')
    def plate_number_change(self):
        if self.plate_number :
            if not self.plate_number.isalnum():
                raise Warning("Plat Number hanya boleh huruf dan angka !")
            self.plate_number = self.plate_number.upper().replace(' ','')

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('plate_number',False):
                vals['plate_number'] = str(vals['plate_number']).replace(" ","").upper()
                if not str(vals['plate_number']).isalnum():
                    raise Warning("Nomor polisi hanya boleh huruf dan angka")
                if len(vals['plate_number']) > 11:
                    raise Warning("Nomor polisi expedisi lebih dari 11 karakter")
        return super(TWVehicle, self).create(vals_list)

    # 13: action methods

    # 14: private methods
    def name_get(self):
        if self._context is None:
            self._context = {}
        res = []
        for record in self:
            title = "[%s] %s" % (record.plate_number, record.partner_id.name)
            res.append((record.id, title))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|',('plate_number', operator, name),('partner_id.name', operator, name)] + args
        categories = self.search(args, limit=limit)
        return categories.name_get()
    
