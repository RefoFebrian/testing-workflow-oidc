# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError as Warning


import logging
_logger = logging.getLogger(__name__)


class ProfitBeforeTax(models.Model):
    _name = "tw.profit.before.tax"
    _description = "Profit Before Tax"

    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return [company_ids[0].id]
        return False

    name = fields.Char(string="Name", help="")
    opex_avg = fields.Float('Opex AVG')
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    period_time_formated = fields.Char(string='Periode', compute='_compute_period_time_formated', store=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')

    total_unit = fields.Float(string='Total Unit M', compute='_compute_all', store=True)
    total_cash = fields.Float(string='Total Cash M', compute='_compute_all', store=True)
    total_cash_lm = fields.Float(string='Total Cash LM', compute='_compute_all', store=True)
    total_credit = fields.Float(string='Total Credit M', compute='_compute_all', store=True)
    total_credit_lm = fields.Float(string='Total Credit LM', compute='_compute_all', store=True)
    total_net_margin = fields.Float(string='Total Net Margin M', compute='_compute_all', store=True)
    pbt_propose = fields.Float(string='PBT Propose M', compute='_compute_all', store=True)
    total_refund = fields.Float(string='Refund M', compute='_compute_all', store=True)
    total_unit_lm = fields.Float(string='Total Unit LM', compute='_compute_all', store=True)
    total_net_margin_lm = fields.Float(string='Total Net Margin LM', compute='_compute_all', store=True)
    pbt_propose_lm = fields.Float(string='PBT Propose LM', compute='_compute_all', store=True)
    total_refund_lm = fields.Float(string='Refund LM', compute='_compute_all', store=True)

    total_cash_show = fields.Char('Total Cash M %', compute='_compute_percentage_sales')
    total_credit_show = fields.Char('Total Credit M %', compute='_compute_percentage_sales')
    total_cash_lm_show = fields.Char('Total Cash LM %', compute='_compute_percentage_sales')
    total_credit_lm_show = fields.Char('Total Credit LM %', compute='_compute_percentage_sales')
    
    # fields on footer excel
    total_net_margin_salesman_cash = fields.Float(string='Net Margin Salesman Cash', compute='_compute_all', store=True)
    total_net_margin_salesman_credit = fields.Float(string='Net Margin Salesman Credit', compute='_compute_all', store=True)
    total_amount_net_margin_salesman = fields.Float(string='Net Margin Salesman Total', compute='_compute_all', store=True)
    
    total_net_margin_counter_cash = fields.Float(string='Net Margin SC Cash', compute='_compute_all', store=True)
    total_net_margin_counter_credit = fields.Float(string='Net Margin SC Credit', compute='_compute_all', store=True)
    total_amount_net_margin_counter = fields.Float(string='Net Margin SC Total', compute='_compute_all', store=True)
    
    total_net_margin_sco_cash = fields.Float(string='Net Margin SCO Cash', compute='_compute_all', store=True)
    total_net_margin_sco_credit = fields.Float(string='Net Margin SCO Credit', compute='_compute_all', store=True)
    total_amount_net_margin_sco = fields.Float(string='Net Margin SCO Total', compute='_compute_all', store=True)
    
    total_all_net_margin_cash = fields.Float(string='Net Margin ALL Cash', compute='_compute_all', store=True)
    total_all_net_margin_credit = fields.Float(string='Net Margin ALL Credit', compute='_compute_all', store=True)
    
    diff_unit = fields.Float(string='Diff. Unit', compute='_compute_diff_unit', store=True)
    diff_pbt = fields.Float(string='Diff. PBT', compute='_compute_diff_pbt', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected')
    ], default='draft')
    is_administrator = fields.Boolean(compute='_compute_administrator')

    # audit trails
    confirm_date = fields.Datetime(string="Confirmed on")
    confirm_uid = fields.Many2one(comodel_name='res.users', string="Confirmed by")
    
    profit_before_tax_line_ids = fields.One2many(comodel_name='tw.profit.before.tax.line', inverse_name='net_margin_id', string='Detail Input Net Margin')
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', default=_get_default_branch)
    area_manager_id = fields.Many2one(comodel_name='hr.employee', string='Area Manager')
    user_id = fields.Many2one(comodel_name='res.users', default=lambda self: self.env.user)
    product_segment_ids = fields.Many2many(comodel_name='product.category', compute='_compute_segment')
    product_category_ids = fields.Many2many(comodel_name='product.category', compute='_compute_category')

    @api.depends('user_id')
    def _compute_administrator(self):
        for record in self:
            record.is_administrator = record.env.user.has_group('tw_profit_before_tax.tw_profit_before_tax_group_admin')

    @api.depends('start_date', 'end_date')
    def _compute_period_time_formated(self):
        for record in self:
            start_date_formated = record.start_date.strftime("%d %b %Y")
            end_date_formated = record.end_date.strftime("%d %b %Y")
            record.period_time_formated = start_date_formated + " - " + end_date_formated

    @api.depends('total_unit', 'total_unit_lm')
    def _compute_diff_unit(self):
        for record in self:
            if record.total_unit and record.total_unit_lm:
                record.diff_unit = record.total_unit - record.total_unit_lm

    @api.depends('pbt_propose', 'pbt_propose_lm')
    def _compute_diff_pbt(self):
        for record in self:
            if record.pbt_propose and record.pbt_propose_lm:
                record.diff_pbt = record.pbt_propose - record.pbt_propose_lm
    
    @api.depends('total_cash', 'total_cash_lm', 'total_credit', 'total_credit_lm', 'total_unit', 'total_unit_lm')
    def _compute_percentage_sales(self):
        self.total_cash_show = f'{self.total_cash} ({round(self.total_cash / self.total_unit * 100, 2) if self.total_unit else 0}%)'
        self.total_credit_show = f'{self.total_credit} ({round(self.total_credit / self.total_unit * 100, 2) if self.total_unit else 0}%)'
        self.total_cash_lm_show = f'{self.total_cash_lm} ({round(self.total_cash_lm / self.total_unit_lm * 100, 2) if self.total_unit_lm else 0}%)'
        self.total_credit_lm_show = f'{self.total_credit_lm} ({round(self.total_credit_lm / self.total_unit_lm * 100, 2) if self.total_unit_lm else 0}%)'
    
    @api.depends('product_category_ids')
    def _compute_segment(self):
        for record in self:
            if record.product_category_ids:
                prod_categ = record.env['product.category']
                segment_ids = prod_categ.search([('parent_id', 'in', record.product_category_ids.ids)]).ids
                record.product_segment_ids = [Command.set(segment_ids)]
    
    @api.depends('division')
    def _compute_category(self):
        for record in self:
            if record.division:
                prod_categ = record.env['product.category']
                division = prod_categ.search([('name', '=', record.division)])
                categ_ids = prod_categ.search([('parent_id', '=', division.id)]).ids
                record.product_category_ids = [Command.set(categ_ids)]

    @api.depends('profit_before_tax_line_ids')
    def _compute_all(self):
        for record in self:
            total_cash = total_cash_lm = 0
            total_credit = total_credit_lm = 0
            total_unit = pbt_propose = total_refund = 0
            total_net_margin = total_all_net_margin_cash = total_all_net_margin_credit = 0
            total_net_margin_salesman_cash = total_net_margin_salesman_credit = total_amount_net_margin_salesman = 0
            total_net_margin_counter_cash = total_net_margin_counter_credit = total_amount_net_margin_counter = 0
            total_net_margin_sco_cash = total_net_margin_sco_credit = total_amount_net_margin_sco = 0
            net_refund = record.env['ir.config_parameter'].get_param('tw_profit_before_tax.default_net_refund')

            for line in record.profit_before_tax_line_ids:
                total_unit += line.ttl_sales
                total_cash += line.amount_unit_cash
                total_cash_lm += line.lm_ttl_sales_cash
                total_credit += line.amount_unit_credit
                total_credit_lm += line.lm_ttl_sales_credit
                total_net_margin += line.all_net_margin_cash + line.all_net_margin_credit
                pbt_propose += (line.all_net_margin_cash + line.all_net_margin_credit) + (net_refund * line.amount_unit_credit) - record.opex_avg
                total_refund += net_refund * line.amount_unit_credit
                total_all_net_margin_cash += line.all_net_margin_cash
                total_all_net_margin_credit += line.all_net_margin_credit
                total_net_margin_salesman_cash += line.net_margin_salesman_cash
                total_net_margin_salesman_credit += line.net_margin_salesman_credit
                total_amount_net_margin_salesman += line.net_margin_salesman_cash + line.net_margin_salesman_credit
                total_net_margin_counter_cash += line.net_margin_counter_cash
                total_net_margin_counter_credit += line.net_margin_counter_credit
                total_amount_net_margin_counter += line.net_margin_counter_cash + line.net_margin_counter_credit
                total_net_margin_sco_cash += line.net_margin_sco_cash
                total_net_margin_sco_credit += line.net_margin_sco_credit
                total_amount_net_margin_sco += line.net_margin_sco_cash + line.net_margin_sco_credit    

            record.total_unit = total_unit
            record.total_cash = total_cash
            record.total_cash_lm = total_cash_lm
            record.total_credit = total_credit
            record.total_credit_lm = total_credit_lm
            record.total_net_margin = total_net_margin
            record.pbt_propose = pbt_propose
            record.total_refund = total_refund
            record.total_all_net_margin_cash = total_all_net_margin_cash
            record.total_all_net_margin_credit = total_all_net_margin_credit
            record.total_net_margin_salesman_cash = total_net_margin_salesman_cash
            record.total_net_margin_salesman_credit = total_net_margin_salesman_credit
            record.total_amount_net_margin_salesman = total_amount_net_margin_salesman
            record.total_net_margin_counter_cash = total_net_margin_counter_cash
            record.total_net_margin_counter_credit = total_net_margin_counter_credit
            record.total_amount_net_margin_counter = total_amount_net_margin_counter
            record.total_net_margin_sco_cash = total_net_margin_sco_cash
            record.total_net_margin_sco_credit = total_net_margin_sco_credit
            record.total_amount_net_margin_sco = total_amount_net_margin_sco
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('profit_before_tax_line_ids'):
                raise Warning('Net Margin details cannot be empty!')

            branch = self.env['res.company']
            sequence = self.env['ir.sequence']
            
            branch = branch.browse(vals.get('company_id'))
            vals['name'] = sequence.get_sequence_code('PBT', branch.code)

        return super().create(vals_list)

    def action_net_margin_list(self):
        domain = False
        company_id = self.env.user.company_ids.ids
        domain = [('state', '!=', 'approved'), ('company_id', 'in', company_id)]
        list_id = self.env.ref('tw_profit_before_tax.view_tw_profit_before_tax_list').id
        form_id = self.env.ref('tw_profit_before_tax.view_tw_profit_before_tax_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Input Net Margin',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.profit.before.tax',
            'views': [(list_id, 'list'), (form_id, 'form')],
            'domain': domain,
            'context': {
                'readonly_by_pass': 1,
                'default_search_draft': 1,
                'default_search_groupby_period_time_formated': 1,
                'group_by': ['period_time_formated']
            }
        }

    def action_net_margin_approval_gm_list(self):
        margin_ids = [margin.id for margin in self.search([('state', '=', 'draft')]) if all([line.state == 'approved' for line in margin.profit_before_tax_line_ids])]
        domain = [('id', 'in', margin_ids)]
        if self.env.user.company_ids:
            domain.append(('company_id','in', self.env.user.company_ids.ids))

        list_id = self.env.ref('tw_profit_before_tax.view_tw_profit_before_tax_gm_approval_list').id
        form_id = self.env.ref('tw_profit_before_tax.view_tw_profit_before_tax_form').id
        search_id = self.env.ref('tw_profit_before_tax.view_tw_profit_before_tax_gm_approval_search').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Approval GM',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.profit.before.tax',
            'views': [(list_id, 'list'), (form_id, 'form')],
            'search_view_id': search_id,
            'domain': domain,
            'context': {
                'readonly_by_pass': 1,
                'default_search_draft': 1,
                'default_search_groupby_period_time_formated': 1,
                'group_by': ['period_time_formated']
            }
        }
    
    def action_confirm(self):
        draft_line = self.profit_before_tax_line_ids.filtered(lambda x: x.state == 'draft')
        if draft_line:
            raise Warning(_("Ensure all record line is approved!"))
        
        self.generate_master_target_margin()
        self.state = 'confirmed'

    def action_reject(self):
        if self.state != 'draft':
            raise Warning(_("Rejection can only be done when state is draft!"))
        
        self.write({ 'state': 'rejected' })

    def generate_master_target_margin(self):
        target_margin = self.env['tw.master.target.margin']
        
        target_sales = target_margin.create_target_margin_from_pbt(self, 'sales')
        target_sc = target_margin.create_target_margin_from_pbt(self, 'sc')
        target_sco = target_margin.create_target_margin_from_pbt(self, 'sco')

        return [ target_sales.id, target_sc.id, target_sco.id ]
        



