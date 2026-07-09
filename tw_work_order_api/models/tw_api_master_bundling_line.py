from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ApiMasterBundlingLine(models.Model):
    _name = "tw.api.master.partner.bundling.line"
    _description = "Master Partner Bundling (Detail)"
    _rec_name = "partner_id"

    branch_bundling_id = fields.Many2one('tw.api.master.partner.bundling', string='Dealer Bundling')
    partner_id = fields.Many2one("res.partner", string="Nama Partner")
    # partner_id = fields.Many2one("res.partner", string="Nama Partner", domain=[('category_id.name','=','Customer')])

    _sql_constraints = [
        ('company_partner_id_uniq', 'unique(branch_bundling_id, partner_id)', "Perhatian!\nPartner sudah ada.")
    ]