# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritWorkOrderNrfs(models.Model):
    _inherit = "tw.work.order"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    nrfs_id = fields.Many2one('tw.nrfs', string='No Case NRFS')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def action_confirm_order(self):
        res = super(InheritWorkOrderNrfs, self).action_confirm_order()
        for wo_obj in self:
            wo_obj._nrfs_update_tgl_selesai(wo_obj)
        return res

    # 13: action methods

    # 14: private methods
    def _nrfs_update_tgl_selesai(self, wo_obj):
        if wo_obj.nrfs_id:
            wo_obj.nrfs_id.write({'act_completion_date': date.today(), 'state': 'done'})
    
    