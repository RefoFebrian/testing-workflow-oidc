# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError as Warning

from datetime import datetime
from dateutil.relativedelta import relativedelta

class ProfitBeforeTaxLine(models.Model):
    _name = "tw.profit.before.tax.line"
    _description = "Profit Before Tax Line"

    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    def _get_default_branch(self):
        return self.env.user.company_ids[0] if self.env.user.company_ids else False
        
    def _get_default_datetime(self): 
        return self.env['res.company'].get_default_datetime()
    
    def _get_year(self):
        current_year = datetime.now().year
        start_year = 2000
        years_available = []

        for x in reversed(range(start_year, current_year + 1)):
            elem = ("{}".format(x), "{}".format(x))
            years_available.append(elem)

        return years_available

    name = fields.Char(required=True, string="Name", help="")
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    period_time_formated = fields.Char(string='Periode', compute='_compute_period_time_formated', store=True)
    
    amount_net_proposed_margin = fields.Integer('Total Net Margin/unit pengajuan')
    lm_amount_net_proposed_margin = fields.Integer('Total Net Margin/unit Actual (LM)')    
    
    salesman_net_proposed_margin = fields.Integer('Salesman Net Margin/unit pengajuan')
    lm_salesman_net_proposed_margin = fields.Integer('Salesman Net Margin/unit Actual (LM)')
    
    counter_net_proposed_margin = fields.Integer('Sales Counter Net Margin/unit pengajuan')
    lm_counter_net_proposed_margin = fields.Integer('Sales Counter Net Margin/unit Actual (LM)')
    
    sco_net_proposed_margin = fields.Integer('SCO Net Margin/unit pengajuan')
    lm_sco_net_proposed_margin = fields.Integer('SCO Net Margin/unit Actual (LM)')
    
    description = fields.Selection([
        ('cek','CEK'),
        ('ok','OK')
    ], 'Description')
    lm_ttl_sales = fields.Integer('TTL Sales LM')
    lm_ttl_sales_cash = fields.Integer('TTL Sales Cash LM')
    lm_ttl_sales_credit = fields.Integer('TTL Sales Credit LM')
    ttl_sales = fields.Integer('TTL Sales (M)')
    
    unit_cash_salesman = fields.Integer('Unit Cash Salesman')
    unit_cash_scounter = fields.Integer('Unit Cash S.Counter')
    unit_cash_sco = fields.Integer('Unit Cash SCO')
    amount_unit_cash = fields.Integer('TTL Unit (Cash)')
    
    unit_credit_salesman = fields.Integer('Unit Credit Salesman')
    unit_credit_scounter = fields.Integer('Unit Credit S.Counter')
    unit_credit_sco = fields.Integer('Unit Credit SCO')
    amount_unit_credit = fields.Integer('TTL Unit (Credit)')

    discount_cash_salesman = fields.Integer('Diskon Cash Salesman')
    discount_cash_counter = fields.Integer('Diskon Cash S.Counter')
    discount_cash_sco = fields.Integer('Diskon Cash SCO')
    amount_discount_cash = fields.Integer('TTL Diskon (Cash)')

    discount_credit_salesman = fields.Integer('Diskon Credit Salesman')
    discount_credit_counter = fields.Integer('Diskon Credit S.Counter')
    discount_credit_sco = fields.Integer('Diskon Credit SCO')
    amount_discount_credit = fields.Integer('TTL Diskon (Credit)')

    gp_bbn = fields.Integer('Gross Profit BBN')
    gp_unit = fields.Integer('Gross Profit Unit')
    ttl_gp = fields.Integer('TTL GP')
    refund = fields.Integer('Refund')
    
    net_margin_salesman_cash = fields.Integer('Net Margin Salesman Cash')
    net_margin_salesman_credit = fields.Integer('Net Margin Salesman Credit')
    amount_net_margin_salesman = fields.Integer('Net Margin Salesman Total')
    
    series_margin_salesman_cash = fields.Integer('Net Margin per Series Salesman Cash', compute='_compute_series_margin_salesman_cash')
    series_margin_salesman_credit = fields.Integer('Net Margin per Series Salesman Credit', compute='_compute_series_margin_salesman_credit')
    lm_series_margin_salesman_cash = fields.Integer('Net Margin per Series Salesman Cash (LM)', compute='_compute_series_margin_salesman_cash')
    lm_series_margin_salesman_credit = fields.Integer('Net Margin per Series Salesman Credit (LM)', compute='_compute_series_margin_salesman_credit')
    
    net_margin_counter_cash = fields.Integer('Net Margin SC Cash')
    net_margin_counter_credit = fields.Integer('Net Margin SC Credit')
    amount_net_margin_counter = fields.Integer('Net Margin SC Total')
    
    series_margin_counter_cash = fields.Integer('Net Margin per Series Sales Counter Cash', compute='_compute_series_margin_counter_cash')
    series_margin_counter_credit = fields.Integer('Net Margin per Series Sales Counter Credit', compute='_compute_series_margin_counter_credit')
    lm_series_margin_counter_cash = fields.Integer('Net Margin per Series Sales Counter Cash (LM)', compute='_compute_series_margin_counter_cash')
    lm_series_margin_counter_credit = fields.Integer('Net Margin per Series Sales Counter Credit (LM)', compute='_compute_series_margin_counter_credit')
    
    net_margin_sco_cash = fields.Integer('Net Margin SCO Cash')
    net_margin_sco_credit = fields.Integer('Net Margin SCO Credit')
    amount_net_margin_sco = fields.Integer('Net Margin SCO Total')
    
    series_margin_sco_cash = fields.Integer('Net Margin per Series SCO Cash', compute='_compute_series_margin_sco_cash')
    series_margin_sco_credit = fields.Integer('Net Margin per Series SCO Credit', compute='_compute_series_margin_sco_credit')
    lm_series_margin_sco_cash = fields.Integer('Net Margin per Series SCO Cash (LM)', compute='_compute_series_margin_sco_cash')
    lm_series_margin_sco_credit = fields.Integer('Net Margin per Series SCO Credit (LM)', compute='_compute_series_margin_sco_credit')
    
    all_net_margin_cash = fields.Float('Net Margin ALL Cash', digits=(16, 2))
    all_net_margin_credit = fields.Float('Net Margin ALL Credit', digits=(16, 2))
    all_net_margin_amount = fields.Float('Net Margin ALL Total', digits=(16, 2))
    
    net_margin_id = fields.Many2one(comodel_name='tw.profit.before.tax', string='Input Net Margin', index=True, ondelete='cascade')
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', default=_get_default_branch)
    series_id = fields.Many2one(comodel_name="product.series",  string="Series",  domain=[('division','=','Unit')],  help="")
    series_motor = fields.Integer()
    year = fields.Selection(selection=_get_year, string='Manufacture Year')
    state = fields.Selection([
        ('draft','Draft'),
        ('rejected','Rejected'),
        ('approved','Approved'),
    ], 'Approval AM')
    
    # Audit Trail
    approve_uid = fields.Many2one('res.users', 'Approved by')
    approve_date = fields.Datetime('Approved on')
    reject_uid = fields.Many2one('res.users', 'Rejected by')
    reject_date = fields.Datetime('Rejected on')
    
    _sql_constraints = [('company_net_margin_series_year', 'unique(net_margin_id, series_id, year)',
                         'Net Margin for this Series and Year already exists')]

    @api.depends('start_date', 'end_date')
    def _compute_period_time_formated(self):
        for record in self:
            start_date_formated = record.start_date.strftime("%d %b %Y")
            end_date_formated = record.end_date.strftime("%d %b %Y")
            record.period_time_formated = start_date_formated + " - " + end_date_formated
            
    @api.depends('net_margin_salesman_cash', 'unit_cash_salesman')
    def _compute_series_margin_salesman_cash(self):
        for record in self:
            record.series_margin_salesman_cash = record.net_margin_salesman_cash / record.unit_cash_salesman if record.unit_cash_salesman else 0
            prev = self._get_previous_pbt(record)
            record.lm_series_margin_salesman_cash = prev.net_margin_salesman_cash / prev.unit_cash_salesman if prev.unit_cash_salesman else 0
    
    @api.depends('net_margin_counter_cash', 'unit_cash_scounter')
    def _compute_series_margin_counter_cash(self):
        for record in self:
            record.series_margin_counter_cash = record.net_margin_counter_cash / record.unit_cash_scounter if record.unit_cash_scounter else 0
            prev = self._get_previous_pbt(record)
            record.lm_series_margin_counter_cash = prev.net_margin_counter_cash / prev.unit_cash_scounter if prev.unit_cash_scounter else 0
    
    @api.depends('net_margin_sco_cash', 'unit_cash_sco')
    def _compute_series_margin_sco_cash(self):
        for record in self:
            record.series_margin_sco_cash = record.net_margin_sco_cash / record.unit_cash_sco if record.unit_cash_sco else 0
            prev = self._get_previous_pbt(record)
            record.lm_series_margin_sco_cash = prev.net_margin_sco_cash / prev.unit_cash_sco if prev.unit_cash_sco else 0

    @api.depends('net_margin_salesman_credit', 'unit_credit_salesman')
    def _compute_series_margin_salesman_credit(self):
        for record in self:
            record.series_margin_salesman_credit = record.net_margin_salesman_credit / record.unit_credit_salesman if record.unit_credit_salesman else 0
            prev = self._get_previous_pbt(record)
            record.lm_series_margin_salesman_credit = prev.net_margin_salesman_credit / prev.unit_credit_salesman if prev.unit_credit_salesman else 0
    
    @api.depends('net_margin_counter_credit', 'unit_credit_scounter')
    def _compute_series_margin_counter_credit(self):
        for record in self:
            record.series_margin_counter_credit = record.net_margin_counter_credit / record.unit_credit_scounter if record.unit_credit_scounter else 0
            prev = self._get_previous_pbt(record)
            record.lm_series_margin_counter_credit = prev.net_margin_counter_credit / prev.unit_credit_scounter if prev.unit_credit_scounter else 0
    
    @api.depends('net_margin_sco_credit', 'unit_credit_sco')
    def _compute_series_margin_sco_credit(self):
        for record in self:
            record.series_margin_sco_credit = record.net_margin_sco_credit / record.unit_credit_sco if record.unit_credit_sco else 0
            prev = self._get_previous_pbt(record)
            record.lm_series_margin_sco_credit = prev.net_margin_sco_credit / prev.unit_credit_sco if prev.unit_credit_sco else 0
    
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
            

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            branch = self.env['res.company']
            sequence = self.env['ir.sequence']
            series = self.env['product.series'].browse(vals.get('series_id'))
            
            branch = branch.browse(vals.get('company_id'))
            vals['name'] = sequence.get_sequence_code(f'PBTL/{series.name}', branch.code)

        return super().create(vals_list)

    def action_approve(self):
        ids = self.env.context.get('active_ids', [self.id])
        for id in ids:
            record = self.browse(id)
            if record.state != 'draft':
                raise Warning('Hanya bisa approve saat status Draft.')
            
            record.write({
                'state': 'approved',
                'approve_uid': record.env.uid,
                'approve_date': datetime.now()
            })

    def action_reject(self):
        self.write({
            'state': 'rejected',
            'reject_uid': self._uid,
            'reject_date': self._get_default_datetime()
        })

    def action_profit_before_tax_line_list(self):
        domain = [('state','=','draft')]
        if self.env.user.company_ids:
            domain.append(('company_id','in', self.env.user.company_ids.ids))
        list_id = self.env.ref('tw_profit_before_tax.view_tw_profit_before_tax_line_list').id
        form_id = self.env.ref('tw_profit_before_tax.view_tw_profit_before_tax_line_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Approval AM',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.profit.before.tax.line',
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
            'context': {
                'readonly_by_pass': 1,
                'default_search_groupby_period_time_formated': 1,
                'group_by': ['period_time_formated']
            }
        }
    
    def _get_previous_pbt(self, record):
        lomonth = record.start_date - relativedelta(days=1)
        folmonth = lomonth.replace(day=1)
        return record.search([('start_date', '=', folmonth),
                              ('end_date', '=', lomonth),
                              ('state', '=', 'approved'),
                              ('year', '=', record.year),
                              ('series_id', '=', record.series_id.id),
                              ('company_id', '=', record.company_id.id)], limit=1)
