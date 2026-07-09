# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib
from datetime import date, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo import Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAssetDisposal(models.Model):
    _name = "tw.asset.disposal"
    _description = 'Disposal Asset'
    _order = "id desc"
    
    # 7: defaults methods
    def _get_default_date(self):
        return date.today()
    
    # 8: fields
    name = fields.Char(string='No', compute='_compute_name', store=True)
    date = fields.Date(string="Date", required=True, readonly=True, default=_get_default_date)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(name='Umum'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled')
    ], string='State', readonly=True, default='draft')

    type = fields.Selection([
        ('sold', 'Sold'),
        ('scrap', 'Scrap')
    ], string="Type", default='scrap')
    tax_totals = fields.Binary(compute='_compute_tax_totals', exportable=False)
    amount_total = fields.Float(string='Amount Total', digits='Account', store=True, compute='_compute_amount')
    amount_tax = fields.Float(string='Amount Tax', digits='Account', store=True, compute='_compute_amount')
    amount_untaxed = fields.Float(string='Untaxed Amount', digits='Account', store=True, compute='_compute_amount')
    invoice_number = fields.Char(string='Invoice Number')
    due_date = fields.Date(string='Due Date')
    notes = fields.Text(string='Notes')

    # Audit Trail
    confirm_uid = fields.Many2one('res.users', string="Confirmed by")
    confirm_date = fields.Datetime('Confirmed on')

    # 9: relation fields
    move_id = fields.Many2one('account.move', string='Account Entry', copy=False)
    move_ids = fields.One2many('account.move.line', related='move_id.line_ids', string='Journal Items', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    disposal_line = fields.One2many('tw.asset.disposal.line', 'disposal_id', string='Disposal Line')
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('company_id','parent_of',company_id)]")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    company_id = fields.Many2one('res.company', string='Branch')    
    disposal_line_sold_ids = fields.One2many('tw.asset.disposal.line', 'disposal_id', string='Disposal Sold Line', domain=[('type', '=', 'sold')], context={'default_type': 'sold'})
    disposal_line_scrap_ids = fields.One2many('tw.asset.disposal.line', 'disposal_id', string='Disposal Scrap Line', domain=[('type', '=', 'scrap')], context={'default_type': 'scrap'})
                
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for data in self:
            if data.id and not data.name and data.state:
                data.name = self.env['ir.sequence'].get_sequence_code('DA',data.company_id.code)

    @api.depends('tax_totals', 'disposal_line.amount', 'disposal_line.amount_subtotal', 'disposal_line.tax_id', 'type')
    def _compute_amount(self):
        for record in self:
            if record.type == 'sold' and record.tax_totals:
                dt = record.tax_totals
                if isinstance(dt, str):
                    import json
                    dt = json.loads(dt)
                record.amount_untaxed = dt.get('base_amount', 0.0)
                record.amount_tax = dt.get('tax_amount', 0.0)
                record.amount_total = dt.get('total_amount', 0.0)
            else:
                untaxes = sum(x.amount_subtotal for x in record.disposal_line)
                record.amount_untaxed = untaxes
                record.amount_tax = 0.0
                record.amount_total = untaxes
    
    @api.depends_context('lang')
    @api.depends('disposal_line_sold_ids.amount', 'disposal_line_sold_ids.tax_id')
    def _compute_tax_totals(self):
        AccountTax = self.env['account.tax']
        for order in self:
            if not order.company_id:
                order.tax_totals = order._empty_tax_totals(order.company_id.currency_id)
                continue

            order_lines = order.disposal_line_sold_ids
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            order.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.company_id.currency_id,
                company=order.company_id,
            )

    @api.onchange('type')
    def onchange_type(self):
        self.disposal_line_sold_ids = False
        self.disposal_line_scrap_ids = False

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):    
        for vals in vals_list:
            vals['date'] = self._get_default_date()           
            if not vals.get('disposal_line_scrap_ids') and not vals.get('disposal_line_sold_ids'):
                raise Warning("Disposal Detail harus diisi !")
        return super(TwAssetDisposal, self).create(vals_list)
    
    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise Warning("Disposal Asset tidak bisa didelete dalam State selain 'draft' !")
        return super(TwAssetDisposal, self).unlink()

    # 13: action methods
    def action_print_asset_disposal(self):
        self.ensure_one()
        return self.env.ref('tw_asset_disposal.action_print_disposal_asset').report_action(self)
        
    def action_confirm(self):
        currency = self.payment_term_id.company_id.currency_id or self.env.company.currency_id
        payment_term = self.payment_term_id._compute_terms(
                    date_ref=self.date or fields.Date.context_today(self),
                    currency=currency,
                    company=self.env.company,
                    tax_amount=0,
                    tax_amount_currency=0,
                    untaxed_amount=self.amount_total,
                    untaxed_amount_currency=self.amount_total,
                    sign=1)

        due_date = payment_term.get('date',self.date)
        self._create_account_move()
        self.write({'confirm_uid':self._uid,
                    'confirm_date':datetime.now(),
                    'date':datetime.now(),
                    'due_date' : due_date,
                    'state' : 'confirm'
                    })
                
        for x in self.disposal_line :
            x.asset_id.write({'disposal_id':self.id,'state':'disposed'})

    # 14: private methods
    def _create_account_move(self):
        if self.move_ids:
            raise Warning(_("Advance Payment already posted or Journal Entry already created."))
        
        branch_config = self.company_id.branch_setting_id.account_setting_id              
        if not branch_config :
            raise Warning("Branch Config %s tidak ditemukan !" % (self.company_id.code))  
        
        journal_id = branch_config.journal_disposal_asset_id
        currency_id = self.company_id.currency_id.id
        move_vals = {
            'move_type': 'entry',
            'ref': self.name,
            'date': self.date,
            'journal_id': journal_id.id,
            'company_id': self.company_id.id,
            'division': self.division,
            'partner_id': self.partner_id.id,
            'currency_id': currency_id,
            'line_ids': [
                Command.create(line_vals)
                for line_vals in self._prepare_move_line_default_vals()
            ],
        }
        if self.name:
            move_vals['name'] = self.name

        move_created = self.env['account.move'].create([move_vals])
        move_created.action_post()
        
        self.move_id = move_created.id
    
    def _prepare_move_line_default_vals(self):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        
        currency_id = self.company_id.currency_id.id
        period_ids = self.env['tw.account.period']._get_current_periods()
        line_vals_list = []       
        if self.type == 'sold' :
            line_vals_list = self._prepare_move_line_sold_vals()
        elif self.type == 'scrap' :
            line_vals_list = self._prepare_move_line_scrap_vals()
                
        
        return line_vals_list
    
    def _prepare_move_line_sold_vals(self):
        line_vals_list = []
        currency_id = self.company_id.currency_id
        period_ids = self.env['tw.account.period']._get_current_periods()
        for asset in self.disposal_line:
            branch_config = self.company_id.branch_setting_id.account_setting_id
            journal_line_id = branch_config.journal_disposal_asset_id.id
            if not journal_line_id :
                raise Warning("Journal Disposal Asset belum diisi dalam Branch Config %s" % (asset.asset_id.company_id.name))
                        
            or_account_id = branch_config.journal_disposal_asset_id.default_debit_account_id.id
            if not or_account_id :
                raise Warning("Debit Account Journal Disposal Asset belum diisi dalam Branch Config %s" % (asset.asset_id.company_id.name))
                        
            akumulasi_account_id = asset.asset_id.category_id.account_depreciation_id.id
            if not akumulasi_account_id :
                raise Warning("Depreciation Account belum diisi dalam category asset %s" % (asset.asset_id.category_id.name))
                        
            asset_account_id = asset.asset_id.category_id.account_asset_id.id
            if not asset_account_id :
                raise Warning("Asset Account belum diisi dalam category asset %s" % (asset.asset_id.category_id.name))
            
            
            account_gain_loss_id = branch_config.account_gain_loss_id.id
            if not account_gain_loss_id :
                raise Warning("Gain/Loss Account belum diisi dalam Branch Config %s" % (asset.asset_id.company_id.name))            
            
            tax_compute = asset.tax_id.compute_all(asset.amount,currency_id)
            other_receivable_value = tax_compute.get('total_included')
            acc_depreciation_value = asset.asset_id.real_purchase_value - asset.asset_id.value_residual
            fixed_asset_value = asset.asset_id.real_purchase_value
            gain_loss_value = asset.amount_subtotal - asset.asset_id.value_residual
            
            # create move line OR
            line_vals_list.append(
                {
                    'name': asset.asset_id.name + '-Other Receivable',
                    'date_maturity': self.due_date,
                    'amount_currency': other_receivable_value,
                    'currency_id': currency_id.id,
                    'debit': other_receivable_value,
                    'credit': 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': or_account_id,
                    'company_id':asset.asset_id.company_id.id,
                    'division': self.division,
                }
            )
            
            # create move line Akumulasi
            line_vals_list.append(
                {
                    'name': asset.asset_id.name + '-Accumulation',
                    'date_maturity': self.due_date,
                    'amount_currency': acc_depreciation_value,
                    'currency_id': currency_id.id,
                    'debit': acc_depreciation_value,
                    'credit': 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': akumulasi_account_id,
                    'company_id': asset.asset_id.company_id.id,
                    'division': self.division,
                }
            )
            
            # create move line Fixed Asset
            line_vals_list.append(
                {
                    'name': asset.asset_id.name + '-Asset',
                    'date_maturity': self.due_date,
                    'amount_currency': -fixed_asset_value,
                    'currency_id': currency_id.id,
                    'debit': 0.0,
                    'credit': fixed_asset_value,
                    'partner_id': self.partner_id.id,
                    'account_id': asset_account_id,
                    'company_id': asset.asset_id.company_id.id,
                    'division': self.division,
                }
            )
            
            # create move line Gain/Loss
            line_vals_list.append(
                {
                    'name': asset.asset_id.name + '-Gain/Loss',
                    'date_maturity': self.due_date,
                    'amount_currency': -gain_loss_value,
                    'currency_id': currency_id.id,
                    'debit': abs(gain_loss_value) if gain_loss_value < 0.0 else 0.0,
                    'credit': gain_loss_value if gain_loss_value > 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': account_gain_loss_id,
                    'company_id': asset.asset_id.company_id.id,
                    'division': self.division,
                }
            )
            
            if asset.tax_id:
                for tax in tax_compute.get('taxes'):
                    tax_account_id = tax.get('account_id')
                    tax_amount = tax.get('amount')
                    tax_name = tax.get('name')
                    # create move line Tax
                    line_vals_list.append(
                        {
                            'name': asset.asset_id.name + '-' + tax_name,
                            'date_maturity': self.due_date,
                            'amount_currency': -tax_amount,
                            'currency_id': currency_id.id,
                            'debit': 0.0,
                            'credit': tax_amount,
                            'partner_id': self.partner_id.id,
                            'account_id': tax_account_id,
                            'company_id': asset.asset_id.company_id.id,
                            'division': self.division,
                        }
                    )
        return line_vals_list

    def _prepare_move_line_scrap_vals(self):
        line_vals_list = []
        currency_id = self.company_id.currency_id.id
        period_ids = self.env['tw.account.period']._get_current_periods()
        for asset in self.disposal_line:
            branch_config = self.company_id.branch_setting_id.account_setting_id
            akumulasi_account_id = asset.asset_id.category_id.account_depreciation_id.id
            if not akumulasi_account_id :
                raise Warning("Depreciation Account belum diisi dalam category asset %s" %(asset.asset_id.category_id.name))
                    
            asset_account_id = asset.asset_id.category_id.account_asset_id.id
            if not asset_account_id :
                raise Warning("Asset Account belum diisi dalam category asset %s"%(asset.asset_id.category_id.name))  
                                
            account_expense_asset_id = branch_config.account_expense_asset_id.id
            if not account_expense_asset_id :
                raise Warning("Expense Account belum diisi dalam Branch Config %s"%(asset.asset_id.company_id.name))
                            
            value_residual = asset.asset_id.value_residual
            gross_value = asset.asset_id.real_purchase_value
            akumulasi_value = gross_value - value_residual
            # create move line akumulasi
            line_vals_list.append(
                {
                    'name': asset.asset_id.name + '-Accumulation',
                    'partner_id': self.partner_id.id,
                    'account_id': akumulasi_account_id,
                    'period_id': period_ids.id,
                    'date': self._get_default_date(),
                    'debit': akumulasi_value,
                    'credit': 0.0,
                    'amount_currency': akumulasi_value,
                    'company_id': asset.company_id.id,
                    'division': self.division,
                    'currency_id': currency_id,
                    'date_maturity': self._get_default_date(),
                }
            )

            # create move line asset
            line_vals_list.append(
                {
                    'name': asset.asset_id.name + '-Asset',
                    'partner_id': self.partner_id.id,
                    'account_id': asset_account_id,
                    'period_id': period_ids.id,
                    'date': self._get_default_date(),
                    'debit': 0.0,
                    'credit': gross_value,
                    'amount_currency': -gross_value,
                    'company_id': asset.company_id.id,
                    'division': self.division,
                    'currency_id': currency_id,
                    'date_maturity': self._get_default_date(),
                }
            )

            # create move line expense
            line_vals_list.append(
                {
                    'name': asset.asset_id.name + '-Expense',
                    'partner_id': self.partner_id.id,
                    'account_id': account_expense_asset_id,
                    'period_id': period_ids.id,
                    'date': self._get_default_date(),
                    'debit': value_residual,
                    'credit': 0.0,
                    'amount_currency': value_residual,
                    'company_id': asset.company_id.id,
                    'division': self.division,
                    'currency_id': currency_id,
                    'date_maturity': self._get_default_date(),
                }
            )
        return line_vals_list
    
    def _empty_tax_totals(self, currency):
        return {
            "currency_id": currency.id,
            "currency_pd": 0.0,
            "company_currency_id": currency.id,
            "company_currency_pd": 0.0,
            "has_tax_groups": False,
            "subtotals": [
                {
                    "tax_groups": [],
                    "tax_amount_currency": 0.0,
                    "tax_amount": 0.0,
                    "base_amount_currency": 0.0,
                    "base_amount": 0.0,
                    "name": "Untaxed Amount"
                }
            ],
            "base_amount_currency": 0.0,
            "base_amount": 0.0,
            "tax_amount_currency": 0.0,
            "tax_amount": 0.0,
            "same_tax_base": False,
            "total_amount_currency": 0.0,
            "total_amount": 0.0
        }

   

    