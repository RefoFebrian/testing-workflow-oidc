# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockMove(models.Model):
    _inherit = "stock.move"
    
    _description = "Stock Move"
    
    # 7: defaults methods

    # 8: fields
    
    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    # @api.model_create_multi
    # def create(self,vals_list):
    #     return super(InheritStockMove, self).create(vals_list)
    
    # def write(self,vals):
    #     return super(InheritStockMove, self).write(vals)

    # 13: action methods
    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        res = super()._prepare_account_move_vals(credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost)
        if res:
            res.update({
                'company_id':self.picking_id.company_id.id or self.company_id.id,
                'division':self.picking_id.division or self.division,
            })
            if self.picking_id:
                ref = self.picking_id.name
                if self.picking_id.batch_id:
                    ref = self.picking_id.batch_id.name + " - " + ref

                res.update({
                    'ref': ref
                })
        return res
    
    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, svl_id, description):
        res = super()._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, svl_id, description)
        if res:
            for vals in res:
                vals[2].update({
                    'company_id':self.picking_id.company_id.id or self.company_id.id,
                    'division':self.picking_id.division or self.division
                })
        return res

    # 14: private methods
    
