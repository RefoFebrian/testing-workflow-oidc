# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, Command, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwSaleOrderLine(models.Model):
    _inherit = "tw.dealer.sale.order.line"
    
    # 7: defaults methods

    # 8: fields
    amount_subsidy = fields.Float(compute='_compute_amount_subsidy', string="Program Subsidy",help="Total of program subsidy amount given for Customer",store=True)
    amount_subsidy_md = fields.Float(compute='_compute_amount_subsidy', string="PS MD",help="Total of program subsidy amount given by Main Dealer",store=True)
    amount_subsidy_finco = fields.Float(compute='_compute_amount_subsidy', string="PS Finco",help="Total of program subsidy amount given by Finance Company",store=True)
    amount_subsidy_dealer = fields.Float(compute='_compute_amount_subsidy', string="PS Dealer",help="Total of program subsidy amount given by Dealer",store=True)
    amount_subsidy_diff_md = fields.Float(compute='_compute_amount_subsidy', string="PS MD Diff",help="Difference of program subsidy amount given by Main Dealer",store=True)
    amount_subsidy_diff_finco = fields.Float(compute='_compute_amount_subsidy', string="PS Finco Diff",help="Difference of program subsidy amount given by Finance Company",store=True)
    
    # 9: relation fields
    available_sales_program_ids = fields.Many2many('tw.sales.program', string='Available Sales Program', compute='_compute_available_sales_program_ids', help='For domain')
    sales_program_ids = fields.One2many(comodel_name='tw.dealer.sale.order.line.program', inverse_name='order_line_id', string="Order Line Discount")
	
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
    @api.depends('gross_profit_unit', 'gross_profit_bbn', 'tax_id', 'amount_subsidy_diff_md', 'amount_subsidy_diff_finco')
    def _compute_net_margin(self):
        """
        Compute the net margin for each sale order line.
        The net margin is calculated as the gross profit unit plus the total included taxes.
        """
        super()._compute_net_margin()
        for line in self:
            line.net_margin = line.net_margin + line.amount_subsidy_diff_md + line.amount_subsidy_diff_finco
            
    @api.depends('order_id.company_id','order_id.finco_id','product_id')
    def _compute_available_sales_program_ids(self):
        for line in self:
            today = date.today()
            branch = line.order_id.company_id

            # Cari Headernya dulu
            domain = [
                ('active', '=', True),
                ('company_id', 'in', [branch.id, branch.parent_id.id] if branch.parent_id else [branch.id]),
                ('start_date', '<=', today),
                ('end_date', '>=', today),
                ('state', '=', 'approved'),
                ('sales_program_type_id.value', '=', 'Program Subsidi'),
            ]
            if line.order_id.finco_id:
                domain += ['|',('finco_id', 'in', [line.order_id.finco_id.id]),('finco_id', '=', False)]
            else:
                domain += [('finco_id', '=', False)]    
            available_sp = self.env['tw.sales.program'].search(domain)

            # Cari Line nya setelah dapat headernya
            domain_line = [('sales_program_id', 'in', available_sp.ids),('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)]
            if not line.order_id.finco_id:
                domain_line += [('discount_finco', '=', 0),('dp_type', '=', False)]
            elif line.order_id.finco_id:
                domain_line += [
                    '|', 
                    '|', 
                    ('dp_type', '=', False),
                    '&', ('dp_type', '=', 'max'), ('amount_dp', '>=', line.downpayment),
                    '&', ('dp_type', '=', 'min'), ('amount_dp', '<=', line.downpayment),
                ]

            available_sp_line = self.env['tw.sales.program.line'].search(domain_line)
            line.available_sales_program_ids = [(6, 0, available_sp_line.mapped('sales_program_id.id'))]

    @api.depends('sales_program_ids', 'sales_program_ids.amount_diff_md', 'sales_program_ids.amount_diff_finco')
    def _compute_amount_subsidy(self):
        for line in self:
            amount_subsidy = amount_subsidy_md = amount_subsidy_finco = amount_subsidy_dealer = amount_subsidy_diff_md = amount_subsidy_diff_finco = 0
            for disc in line.sales_program_ids:
                amount_subsidy += disc.discount_customer
                amount_subsidy_md += disc.amount_md + disc.amount_ahm
                amount_subsidy_dealer += disc.amount_dealer
                amount_subsidy_finco += disc.amount_finco
                amount_subsidy_diff_md += disc.amount_diff_md
                amount_subsidy_diff_finco += disc.amount_diff_finco

            line.recompute_helper += 1
            line.amount_subsidy_md = amount_subsidy_md
            line.amount_subsidy_dealer = amount_subsidy_dealer
            line.amount_subsidy_finco = amount_subsidy_finco
            line.amount_subsidy_diff_md = amount_subsidy_diff_md
            line.amount_subsidy_diff_finco = amount_subsidy_diff_finco
            line.amount_subsidy = amount_subsidy

    @api.depends('sales_program_ids.discount_customer', 'discount_regular')
    def _compute_total_discount(self):
        for line in self:
            discount_total = sum([d.discount_customer for d in line.sales_program_ids])
            line.discount_total = line.discount_regular + discount_total

    @api.onchange('downpayment')
    def _onchange_downpayment(self):
        self.sales_program_ids = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.sales_program_ids = False
        super()._onchange_product_id()

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for order_line in res:
            order_line._validate_sales_program()
        return res

    def write(self, vals):
        res = super().write(vals)
        for order_line in self:
            order_line._validate_sales_program()
        return res

    # 13: action methods
	
    # 14: private methods
    def _validate_sales_program(self):
        self.ensure_one()
        if self.sales_program_ids:
            programs = self.sales_program_ids.mapped('sales_program_id')
            if len(programs) != len(self.sales_program_ids):
                raise Warning("Sales Program tidak boleh duplikat! Silahkan periksa inputan sales program")
    
    def _get_price_after_discount(self):
        self.ensure_one()
        price = super()._get_price_after_discount()
        # Harga dikurang dengan subsidi jika ada
        return price - self.amount_subsidy


    def _get_amount_dealer_expense(self):
        total = super()._get_amount_dealer_expense()
        total += self.amount_subsidy_dealer
        return total
    
    def _get_total_discount(self):
        discount = super()._get_total_discount()
        discount += self.amount_subsidy
        return discount

    def create_subsidy_invoice(self):
        self.ensure_one()
        invoices = self.env['account.move']
        for program in self.sales_program_ids:
            invoices += self._create_finco_subsidy_invoice(program)
            invoices += self._create_md_subsidy_invoice(program)
        return invoices
            
    def _create_finco_subsidy_invoice(self, program):
        discount_gap = 0
        invoice = self.env['account.move']
        if program.amount_finco > 0:
            if program.discount_customer != program.discount_amount:
                discount = program.discount_amount - program.amount_dealer if program.amount_dealer else program.discount_amount
                discount_gap = discount - program.discount_customer
            
            account_conf = self.company_id.branch_setting_id.account_setting_id
            if not account_conf.journal_dso_subsidy_finco_id:
                raise Warning(_("The Journal Subsidi Finco is not configured!\n"
                                "Please configure it in the Branch Settings."))
            
            if not account_conf.account_dso_remaining_subsidy_id:
                raise Warning(_("The Account for Sisa Program Subsidi is not configured!\n"
                                "Please configure it in the Branch Settings."))
            
            journal_subsidy_finco = account_conf.journal_dso_subsidy_finco_id
            if not journal_subsidy_finco:
                raise Warning('Konfigurasi Journal Subsidi Finco pada branch %s belum disetting!' %(self.company_id.branch_setting_id.name))
            
            invoice_subsidy_finco_line = []
            code = journal_subsidy_finco.code
            prefix = self.company_id.code
            invoice_subsidy_finco = self.order_id._prepare_invoice()
            invoice_subsidy_finco.update({
                'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
                'journal_id': journal_subsidy_finco.id,
                'company_id': self.order_id.company_id.id,
                'move_type': 'out_invoice',
                'partner_id': self.order_id.finco_id.id,
                'partner_shipping_id': self.order_id.finco_id.id,
            })
            
            if discount_gap > 0:
                if program.amount_finco > discount_gap: 
                    discount_finco = program.amount_finco - discount_gap
                    discount_oi = discount_gap
                elif program.amount_finco == discount_gap:
                    discount_finco = program.amount_finco
                else:
                    discount_oi = discount_gap - program.amount_finco
                    discount_finco = program.amount_finco - discount_oi
                    discount_gap = discount_gap - discount_oi
                
                if discount_finco > 0:   
                    invoice_subsidy_finco_line.append(Command.create(self._prepare_invoice_line(**{
                        'name': f'Subsidy {program.sales_program_id.name} {self.product_id.name}',
                        'company_id': self.order_id.company_id.id,
                        'product_id': False,
                        'tax_ids': False,
                        'quantity': 1,
                        'discount': 0,
                        'price_unit': discount_finco,
                        'account_id': journal_subsidy_finco.default_credit_account_id.id
                    })))
                
                if discount_oi > 0:
                    invoice_subsidy_finco_line.append(Command.create(self._prepare_invoice_line(**{
                        'name': f'Remaining subsidy {program.sales_program_id.name} {self.product_id.name}',
                        'company_id': self.order_id.company_id.id,
                        'product_id': False,
                        'tax_ids': False,
                        'quantity': 1,
                        'discount': 0,
                        'price_unit': discount_oi,
                        'account_id': account_conf.account_dso_remaining_subsidy_id.id
                    })))
                
            else:
                invoice_subsidy_finco_line.append(Command.create(self._prepare_invoice_line(**{
                    'name': f'Subsidy {program.sales_program_id.name} {self.product_id.name}',
                    'company_id': self.order_id.company_id.id,
                    'product_id': False,
                    'tax_ids': False,
                    'quantity': 1,
                    'discount': 0,
                    'price_unit': program.amount_finco,
                    'account_id': journal_subsidy_finco.default_credit_account_id.id
                })))
                
            invoice_subsidy_finco['invoice_line_ids'] = invoice_subsidy_finco_line
            invoice = self.order_id._create_account_invoices([invoice_subsidy_finco], final=True)
        return invoice


    def _create_md_subsidy_invoice(self, program):
        invoice = self.env['account.move']
        if (program.amount_md > 0 or program.amount_ahm > 0):
            discount_gap = 0
            finco_refund = False
            if program.discount_customer != program.discount_amount:
                discount = program.discount_amount - program.amount_dealer if program.amount_dealer else program.discount_amount
                discount_gap = discount - program.discount_customer
                if discount_gap <= 0:
                    finco_refund = True
                elif program.amount_finco > discount_gap:
                    finco_refund = True

            account_conf = self.company_id.branch_setting_id.account_setting_id
            if not account_conf.journal_dso_subsidy_md_id:
                raise Warning(_("The Journal Subsidi MD is not configured!\n"
                                "Please configure it in the Branch Settings."))
            
            journal_subsidy_md = account_conf.journal_dso_subsidy_md_id
            if not journal_subsidy_md.default_credit_account_id or not journal_subsidy_md.default_debit_account_id:
                raise Warning(_(f"The Chart of Accounts configuration for Journal MD {journal_subsidy_md} is incomplete!\n"
                                "Please configure it in the Journal Settings."))
            
            if not self.company_id.default_supplier_id:
                raise Warning(_("The selected company does not have a default supplier configured!"))
            
            invoice_subsidy_md_line = []
            code = journal_subsidy_md.code
            prefix = self.company_id.code
            invoice_subsidy_md = self.order_id._prepare_invoice()
            invoice_subsidy_md.update({
                'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
                'company_id': self.order_id.company_id.id,
                'journal_id': journal_subsidy_md.id,
                'move_type': 'out_invoice',
                'partner_id': self.company_id.default_supplier_id.id,
                'partner_shipping_id': self.company_id.default_supplier_id.id,
            })

            if finco_refund == False:
                if discount_gap > 0:
                    if (program.amount_ahm + program.amount_md) >= discount_gap:
                        discount_md = program.amount_ahm + program.amount_md - discount_gap
                        discount_oi = discount_gap
                    else:
                        discount_md = discount_gap - program.amount_ahm - program.amount_md
                    
                    if discount_md >= 0:  
                        invoice_subsidy_md_line.append(Command.create(self._prepare_invoice_line(**{
                            'name': f'Subsidy {program.sales_program_id.name} {self.product_id.name}',
                            'company_id': self.order_id.company_id.id,
                            'product_id': False,
                            'quantity': 1,
                            'discount': 0,
                            'price_unit': self.tax_id.compute_all(discount_md, quantity=1)['total_excluded'],
                            'account_id': journal_subsidy_md.default_credit_account_id.id,
                            'tax_ids': False
                        })))
                    
                    if discount_oi > 0:
                        invoice_subsidy_md_line.append(Command.create(self._prepare_invoice_line(**{
                            'name': f'Remaining subsidy {program.sales_program_id.name} {self.product_id.name}',
                            'company_id': self.order_id.company_id.id,
                            'product_id': False,
                            'quantity': 1,
                            'discount': 0,
                            'price_unit': self.tax_id.compute_all(discount_gap, quantity=1)['total_excluded'],
                            'account_id': account_conf.account_dso_remaining_subsidy_id.id,
                            'tax_ids': False
                        })))
                else:
                    invoice_subsidy_md_line.append(Command.create(self._prepare_invoice_line(**{
                        'name': f'Subsidy {program.sales_program_id.name} {self.product_id.name}',
                        'company_id': self.order_id.company_id.id,
                        'product_id': False,
                        'quantity': 1,
                        'discount': 0,
                        'price_unit': self.tax_id.compute_all(program.amount_md + program.amount_ahm, quantity=1)['total_excluded'],
                        'account_id': journal_subsidy_md.default_credit_account_id.id,
                        'tax_ids': False
                    })))
                
            else:
                invoice_subsidy_md_line.append(Command.create(self._prepare_invoice_line(**{
                    'name': f'Subsidy {program.sales_program_id.name} {self.product_id.name}',
                    'company_id': self.order_id.company_id.id,
                    'product_id': False,
                    'quantity': 1,
                    'discount': 0,
                    'price_unit': self.tax_id.compute_all(program.amount_md + program.amount_ahm, quantity=1)['total_excluded'],
                    'account_id': journal_subsidy_md.default_credit_account_id.id,
                    'tax_ids': False
                })))
                    
            invoice_subsidy_md['invoice_line_ids'] = invoice_subsidy_md_line
            invoice = self.order_id._create_account_invoices([invoice_subsidy_md], final=True)
        return invoice
