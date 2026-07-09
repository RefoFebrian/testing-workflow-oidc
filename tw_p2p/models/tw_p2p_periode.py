# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwP2pPeriode(models.Model):
    _name = "tw.p2p.periode"
    _description = "P2P Configuration"
    _order = "name desc"

    # 7: defaults methods

    # 8: fields 
    name = fields.Char(string='Name')
    start_date = fields.Date(string='Effective Start Date')
    end_date = fields.Date(string='Effective End Date')
    periode_start_date = fields.Date(string='Periode Start Date')
    periode_end_date = fields.Date(string='Periode End Date')
    active = fields.Boolean(string='Active', default=True)    
    # 9: relation fields

    # 10: constraints & sql constraints
    _sql_constraints = [
    ('unique_name', 'unique(name)', 'Master data sudah pernah dibuat !'),
    ]  

    # 11: compute/depends & on change methods
        
    @api.onchange('name')
    def onchange_name(self):   
        if self.name :
            if len(self.name) > 6 :
                raise Warning("Name tidak boleh lebih dari 6 digit ! ")
            else :            
                cek = self.name.isdigit()
                if not cek :
                    self.name = False
                    raise Warning('Name hanya boleh angka ! ')
        

    # 12: override methods
    def unlink(self):
        for record in self:
            if record.active:
                record.active = False
            else:
                raise Warning("Master data tidak dapat dihapus !")
        return True
    

    # 13: action methods

    # 14: private methods
