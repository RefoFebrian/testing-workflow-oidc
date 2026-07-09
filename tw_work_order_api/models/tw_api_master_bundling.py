from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ApiMasterBundling(models.Model):
    _name = "tw.api.master.partner.bundling"
    _description = "Master Partner Bundling"
    _rec_name = "company_id"

    @api.model
    def _get_default_branch(self):
        company_ids = self.env.user.company_ids
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False

    company_id = fields.Many2one('res.company', string='Dealer', default=_get_default_branch)
    partner_bundling_ids = fields.One2many('tw.api.master.partner.bundling.line', 'branch_bundling_id', string="Detail Partner Bundling")

    _sql_constraints = [
        ('company_id_uniq', 'unique(company_id)', "Perhatian!\nDealer sudah ada.")
    ]

    @api.constrains('partner_bundling_ids')
    def _check_partner_bundling_empty(self):
        if not self.partner_bundling_ids:
            raise ValidationError('Perhatian!\nPartner Bundling harus diisi.')