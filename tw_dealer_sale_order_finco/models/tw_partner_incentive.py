# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError
from odoo.tools import float_is_zero, groupby

# 5: local imports

# 6: Import of unknown third party lib


class Partner(models.Model):
    _inherit = "res.partner"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    incentive_partner_ids = fields.One2many(comodel_name='tw.incentive.partner.line', inverse_name='partner_id')
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods 


class TwIncentivePartnerLine(models.Model):
    _name = "tw.incentive.partner.line"
    _description = "Incentive Partner Line"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name', required=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    active = fields.Boolean('Active', default=True)

    # 9: relation fields
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', required=True, ondelete="cascade")
    incentive_finco_detail_ids = fields.One2many(comodel_name='tw.incentive.partner.line.detail',
                                                 inverse_name='incentive_finco_line_id', string='Details')
    tax_ids = fields.Many2many(comodel_name='account.tax', relation='tw_incentive_partner_tax_rel',
                               column1='incentive_partner_id', column2='tax_id')

    # 10: constraints & sql constraints
    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError(_("Start Date harus lebih kecil dari atau sama dengan End Date."))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods


class TwIncentivePartnerDetail(models.Model):
    _name = "tw.incentive.partner.line.detail"
    _description = "Incentive Partner Detail"

    # 7: defaults methods

    def _get_default_branch(self):
        return self.env.user.company_ids[0].id if self.env.user.company_ids else False

    # 8: fields
    amount = fields.Float('Incentive Amount')

    # 9: relation fields
    incentive_finco_line_id = fields.Many2one(comodel_name='tw.incentive.partner.line', string='Incentive Line')
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', default=_get_default_branch)
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods