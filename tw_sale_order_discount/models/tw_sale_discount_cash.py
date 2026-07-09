
import re
from odoo import models, fields, api

class MasterDiscountCash(models.Model):
    _name = "tw.sale.discount.cash"
    _description = "Master Discount Cash"
    _rec_names_search = ['name', 'code']

    name = fields.Char('Name', compute='_compute_name')
    code = fields.Char(string='Code', compute='_compute_selection_code', store=True)
    discount_percent = fields.Float(string='Discount %')

    type_id = fields.Many2one('tw.purchase.order.type','Type')
    payment_term_id = fields.Many2one('account.payment.term','Payment Term')

    def _compute_name(self):
        for record in self:
            name = f"[{record.type_id.name}] {record.payment_term_id.name} ({record.discount_percent})"
            record.name = name

    @api.depends('type_id', 'payment_term_id')
    def _compute_selection_code(self):
        for record in self:
            if record.type_id and record.payment_term_id:
                code = f"{record.type_id.name}|{record.payment_term_id.name}"
                record.code = code
            else:
                record.code = self._compute_name()

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            parts = name.split('|', 1)

            if len(parts) == 2:
                code_part = parts[0].strip()
                color_part = parts[1].strip()

                args = [('type_id.name', '=ilike', code_part), ('payment_term_id.name','=ilike',color_part)] + args
            else:
                args = ['|', ('name', operator, name), ('code', operator, name)] + args

        records = self.search(args, limit=limit)
        return [(rec.id, rec.display_name) for rec in records.sudo()]
