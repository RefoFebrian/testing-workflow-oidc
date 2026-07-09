from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TwPettyCashOutLine(models.Model):
    _name = "tw.petty.cash.out.line"
    _description = "Petty Cash Out Line"

    name = fields.Char(string="Description", required=True , compute="_compute_name")
    amount = fields.Float(string="Amount")
    amount_real = fields.Float(string="Amount Real")
    note = fields.Char('Note')
    account_id = fields.Many2one('account.account', string="Account")
    petty_cash_out_id = fields.Many2one('tw.petty.cash.out', string="Petty Cash Out", ondelete='cascade')
    type_id = fields.Many2one(
        comodel_name='tw.petty.cash.type',
        string='Tipe Transaksi',
        required=True)
    type_detail_id = fields.Many2one(
        comodel_name='tw.petty.cash.type.line',
        string='Transaksi Detail',
        required=True)
    
    @api.depends('type_detail_id','note')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.type_detail_id.name or ' '} {rec.note or ' '}"

    @api.onchange('type_id')
    def onchange_type(self):
        self.type_detail_id = False
        self.account_id = False

    @api.onchange('type_id','type_detail_id')
    def onchange_type_and_type_detail(self):
        self.amount = False
        self.note = False

    @api.onchange('type_detail_id', 'account_id')
    def onchange_type_detail(self):
        self.name = self.type_detail_id.name
        self.account_id = self.type_detail_id.account_id.id

    @api.model_create_multi
    def create(self, vals_list):
        seen = set()
        for rec in vals_list:
            type_detail_id = rec.get('type_detail_id')
            petty_cash_out_id = rec.get('petty_cash_out_id')
            amount = rec.get('amount')
            
            if amount and amount <= 0:
                raise ValidationError(
                    "Amount tidak boleh negatif atau 0"
                )

            if type_detail_id in seen:
                raise ValidationError(
                    f"Terdapat duplikat Line dengan Transaksi Detail '{type_detail_id.name}' di record yang sama."
                )
            seen.add(type_detail_id)

            existing_line = self.env['tw.petty.cash.out.line'].search([
                ('petty_cash_out_id', '=', petty_cash_out_id),
                ('type_detail_id', '=', type_detail_id),
            ], limit=1)

            if existing_line:
                raise ValidationError(
                    f"Lines dengan Transaksi Detail '{existing_line.type_detail_id.name}' sudah ada."
                )
        return super(TwPettyCashOutLine, self).create(vals_list)
        
    def recalculate_amount_real(self):
        for rec in self:
            petty_cash_in_line_ids = self.env['tw.petty.cash.in.line'].search([
                ('petty_cash_in_id.petty_cash_out_id', '=', rec.petty_cash_out_id.id),
                ('petty_cash_in_id.state', '=', 'posted'),
                ('account_id', '=', rec.account_id.id),
            ])
            used_amount = sum(petty_cash_in_line_ids.mapped('amount'))
            rec.write({
                'amount_real': rec.amount - used_amount
            })
