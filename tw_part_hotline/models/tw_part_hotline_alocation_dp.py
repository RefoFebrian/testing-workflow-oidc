# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class AlocationDPHotline(models.Model):
    _name = "tw.part.hotline.alocation.dp"
    _description = "TW Part Hotline Alocation DP"

    # 7: defaults methods

    # 8: fields
    amount_hl_original = fields.Float('HL Original')
    amount_hl_balance = fields.Float('HL Balance')
    amount_hl_allocation = fields.Float('Allocation')

    # 9: relation fields
    hotline_id = fields.Many2one('tw.part.hotline',ondelete='cascade')
    hl_id = fields.Many2one('account.move.line','Hutang Lain')

    # 10: constraints & sql constraints
    @api.constrains('hotline_id','hl_id')
    def _check_hotline_hl_unique(self):
        for rec in self:
            if rec.hotline_id and rec.hl_id:
                if self.search([('hotline_id', '=', rec.hotline_id.id), ('hl_id', '=', rec.hl_id.id), ('id', '!=', rec.id)]):
                    raise ValidationError('Hutang Lain tidak boleh duplicat !')

    @api.constrains('amount_hl_allocation')
    def cek_amount_hl_alocation(self):
        if self.amount_hl_allocation:
            if self.amount_hl_allocation > abs(self.hl_id.amount_residual):
                raise Warning('Nilai Alokasi tidak boleh lebih besar dari Amount Balance ! Number %s \n Nilai Amount Residual RP. %s ' %(self.hl_id.ref,abs(self.hl_id.amount_residual)))

    # 11: compute/depends & on change methods
    @api.onchange('hl_id')
    def onchange_hl(self):
        self.amount_hl_original = False
        self.amount_hl_balance = False
        self.amount_hl_allocation = False

        if self.hl_id:
            self.amount_hl_original = abs(self.hl_id.credit)
            self.amount_hl_balance = abs(self.hl_id.amount_residual)
            self.amount_hl_allocation = abs(self.hl_id.amount_residual)