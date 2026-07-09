# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwAssetDisposalHutangLain(models.Model):
    _name = "tw.asset.disposal.hutang.lain"
    _description = "Asset Disposal Hutang Lain"

    # 8: fields
    amount_hl_original = fields.Float('HL Original')
    amount_hl_balance = fields.Float('HL Balance')
    amount_hl_allocation = fields.Float('Allocation')
    
    # 9: relation fields
    disposal_id = fields.Many2one('tw.asset.disposal', 'Disposal Asset')
    hl_id = fields.Many2one('account.move.line','Hutang Lain',copy=False)

    # 10: constraints & sql constraints

    @api.constrains('hl_id', 'amount_hl_allocation')
    def _check_amount_allocation(self):
        for record in self:
            balance = abs(record.hl_id.amount_residual)
            if record.amount_hl_allocation > balance:
                raise Warning(_(f"Alokasi amount tidak boleh melebihi sisa balance. \n\nEntry: {record.hl_id.display_name} \nTotal Alokasi: {record.amount_hl_allocation} \nSisa Balance: {balance}"))
            if record.amount_hl_allocation < 0:
                raise Warning(_("Alokasi amount harus bernilai positif!"))
    
    # 11: compute/depends & on change methods
    @api.onchange('hl_id')
    def _onchange_hl_id(self):
        if self.hl_id and abs(self.hl_id.amount_residual) > 0:
            self.amount_hl_original = self.hl_id.credit
            self.amount_hl_balance = abs(self.hl_id.amount_residual)
            self.amount_hl_allocation = abs(self.hl_id.amount_residual)

    # 12: override methods

    # 13: action methods

    # 14: private methods
