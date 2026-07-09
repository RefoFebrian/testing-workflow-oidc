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



class TwP2pConfig(models.Model):
    _name = "tw.p2p.config"
    _description ="P2P Configuration"
    _rec_name = 'supplier_id'
    
    # 7: defaults methods

    # 8: fields 
    tentative_1 = fields.Integer(string='Tentative 1 (%)')
    tentative_2 = fields.Integer(string='Tentative 2 (%)')
    active = fields.Boolean(string='Active', default=True)
    
    # 9: relation fields
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True, domain="[('category_id.name','=','Principle')]")

    # 10: constraints & sql constraints
    _sql_constraints = [
    ('unique_supplier_id', 'unique(supplier_id)', 'Master data sudah pernah dibuat !'),
    ]    

    # 11: compute/depends & on change methods
    @api.onchange('tentative_1','tentative_2')
    def onchange_tentative(self):
        if self.tentative_1 > 100 :
            self.tentative_1 = 0
            raise Warning("Nilai tentative 1 tidak boleh lebih dari 100% !")
            
        if self.tentative_2 > 100 :
            self.tentative_2 = 0
            raise Warning("Nilai tentative 2 tidak boleh lebih dari 100% !")

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

    
  