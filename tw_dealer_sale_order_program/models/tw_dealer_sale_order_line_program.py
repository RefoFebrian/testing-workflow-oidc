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


class TwSaleOrderProgram(models.Model):
    _name = "tw.dealer.sale.order.line.program"
    _description = "Program Dealer Sale Order"

    # 7: defaults methods

    # 8: fields
    dp_type = fields.Char(string="Subsidi DP Type", compute='_compute_amount_subsidy', store=True)
    subsidy_type = fields.Char(string="Subsidi Type", compute='_compute_amount_subsidy', store=True)
    amount_md = fields.Float(string="Subsidi MD", compute='_compute_amount_subsidy', store=True)
    amount_ahm = fields.Float(string="Subsidi AHM", compute='_compute_amount_subsidy', store=True)
    amount_finco = fields.Float(string="Subsidi FINCO", compute='_compute_amount_subsidy', store=True)
    amount_dealer = fields.Float(string="Subsidi DEALER", compute='_compute_amount_subsidy', store=True)
    amount_others = fields.Float(string="Subsidi OTHERS", compute='_compute_amount_subsidy', store=True)
    amount_diff_md = fields.Float(string="Subsidi MD DIFF", compute='_compute_amount_subsidy', store=True)
    amount_diff_finco = fields.Float(string="Subsidi FINCO DIFF", compute='_compute_amount_subsidy', store=True)
    discount_amount = fields.Float(string='Total Subsidi', compute='_compute_amount_subsidy', store=True, help="Max. discount given by selected subsidy program")
    discount_customer = fields.Float(string='Discount', default=0)
    
    # 9: relation fields
    order_line_id = fields.Many2one(comodel_name='tw.dealer.sale.order.line', ondelete='cascade')
    sales_program_id = fields.Many2one(comodel_name='tw.sales.program',string="Subsidi Program Name")
	
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
    @api.depends('sales_program_id')
    def _compute_amount_subsidy(self):
        for disc in self:
            if not disc.order_line_id.product_id:
                raise Warning(_("You have to select a product before insert a Subsidy/Discount!"))
            
            product_template = disc.order_line_id.product_id.product_tmpl_id
            subsidy_line = disc.sales_program_id.line_ids.filtered(lambda x: x.product_tmpl_id == product_template)

            if subsidy_line.dp_type == 'min' and disc.order_line_id.downpayment < subsidy_line.amount_dp:
                raise Warning(_("Down payment hasn't met minimum requirements of selected program!"))

            elif subsidy_line.dp_type == 'max' and disc.order_line_id.downpayment > subsidy_line.amount_dp:
                raise Warning(_("Down payment can't be greater than maximum requirement limit of selected program!"))
        
            if subsidy_line:
                disc.discount_amount = subsidy_line.discount_total
                disc.discount_customer = subsidy_line.discount_total
                disc.amount_ahm = subsidy_line.discount_ahm
                disc.amount_md = subsidy_line.discount_md
                disc.amount_finco = subsidy_line.discount_finco
                disc.amount_dealer = subsidy_line.discount_dealer
                disc.amount_others = subsidy_line.discount_others
                disc.dp_type = subsidy_line.dp_type
                disc.subsidy_type = disc.sales_program_id.subsidy_type

    @api.onchange('discount_customer')
    def _onchange_discount_customer(self):
        pilot = False
        amount_diff_md = amount_diff_finco = 0

        if self.discount_customer < 0:
            raise Warning(_("Discount Customer can not be negative!"))

        if self.discount_customer > self.discount_amount:
            raise Warning(_("Discount customer can not be greater than Total Subsidy!"))

        if self.dp_type == 'fix':
            self.discount_customer = self.discount_amount
            self.amount_diff_md = amount_diff_md
            self.amount_diff_finco = amount_diff_finco
        else:
            # pilot = self._is_discount_dso_pilot()
            # if pilot:
            disc_diff = self._calculate_discount_difference()
            amount_diff_md = disc_diff.get('amount_diff_md')
            amount_diff_finco = disc_diff.get('amount_diff_finco')
            
            # self.discount_customer = self.discount_customer
            self.amount_diff_md = amount_diff_md
            self.amount_diff_finco = amount_diff_finco

    # 12: override methods

    # 13: action methods
	
    # 14: private methods
    def _is_discount_dso_pilot(self):
        # TODO: do pilot project here
        # pilot_project = self.env['tw.pilot.project'].search([('name', '=', 'Discount DSO')], limit=1)
        # if not pilot_project:
        #     return False

        # sale_order = self.order_line_id.order_id
        # company_id = sale_order.company_id.id

        # if pilot_project.is_active and company_id in pilot_project._generate_available_branch():
        #     return True
        return False

    def _calculate_discount_difference(self):
        amount_diff_finco = amount_diff_md = 0

        diff = (self.amount_ahm + self.amount_md + self.amount_finco) - self.discount_amount
        if diff > 0:
            if self.amount_finco and (self.amount_ahm or self.amount_md):
                amount_diff_finco = diff / 2
                amount_diff_md = diff / 2
            elif self.amount_finco:
                amount_diff_finco = diff
            elif self.amount_ahm or self.amount_md:
                amount_diff_md = diff

        return {'amount_diff_md': amount_diff_md, 'amount_diff_finco': amount_diff_finco}
