from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

    
class ExpeditionPrice(models.Model):
    _name = "tw.expedition.price"
    _description = "Expedition Price"

    name = fields.Char('Name')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    active = fields.Boolean('Active', default=True)

    company_id = fields.Many2one('res.company', string="Branch", domain=[('parent_id', '!=', False)])
    expedition_id = fields.Many2one('res.partner', string="Expedition", domain=[('category_id.name','=','Expedition')])
    expedition_price_ids = fields.One2many('tw.expedition.price.line','expedition_price_id',string='Expedition Price Details')

    @api.onchange("start_date", "end_date")
    def _onchange_end_date(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            self.end_date = False
            return {
                "warning": {
                    "title": "Perhatian!",
                    "message": "End Date tidak boleh lebih kecil dari Start Date.",
                }
            }

    @api.constrains("start_date", "end_date", "active")
    def _check_date(self):
        for record in self:
            if not record.active:
                continue

            overlapping_lines = self.env["tw.expedition.price.line"].search([
                ("expedition_price_id", "=", record.expedition_price_id.id),
                ("active", "=", True),
                ("id", "!=", record.id),
            ])

            for line in overlapping_lines:
                if record.start_date <= line.end_date:
                    raise Warning("You cannot have two pricelist versions that overlap!")

    _sql_constraints = [
        (
            "unique_expedition",
            "unique(company_id, partner_id, reception_city)",
            "The expedition for the Branch and Receiving City already exists! Please check again.",
        ),
    ]