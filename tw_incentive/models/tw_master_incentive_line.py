# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class MasterincentiveLine(models.Model):
    _name = "tw.master.incentive.line"
    _description = "Master Incentive Line"
    _rec_name = "quantity"
    _order = "quantity"
    
    # 7: defaults methods
    
    # 8: fields
    quantity = fields.Integer(string='Quantity', help="The sales quantity will refer to this field to determine the incentive amount.")
    cash = fields.Float(string='Cash', help="Cash sales for the quantity will receive this amount")
    credit = fields.Float(string='Credit', help="Credit sales for the quantity will receive this amount")
    accumulate_cash = fields.Float(string='Accumulate Cash', compute='_compute_accumlated_cash', help="The accumulated cash amount for the incentive line.")
    accumulate_credit = fields.Float(string='Accumulate Credit', compute='_compute_accumlated_credit', help="The accumulated credit amount for the incentive line.")
    reward = fields.Float(string='Reward', help="The reward amount for the incentive line.")

    # 9: relation fields
    incentive_id = fields.Many2one(comodel_name='tw.master.incentive', ondelete='cascade', string='Incentive', help="The master incentive associated with this line.")

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('quantity', 'cash')
    def _compute_accumlated_cash(self):
        for line in self:
            master_lines = line.incentive_id.incentive_line_ids
            line.accumulate_cash = sum([l.cash for l in master_lines.filtered(lambda x: x.quantity <= line.quantity)])

    @api.depends('quantity', 'credit')
    def _compute_accumlated_credit(self):
        for line in self:
            master_lines = line.incentive_id.incentive_line_ids
            line.accumulate_credit = sum([l.credit for l in master_lines.filtered(lambda x: x.quantity <= line.quantity)])
    
    # 12: override methods

    # 13: action methods
    
    # 14: private methods
