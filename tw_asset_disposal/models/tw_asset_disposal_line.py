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
                     
class TwAssetDisposalLine(models.Model):
    _name = "tw.asset.disposal.line"
    _description = 'Disposal Asset Line'
    
    # 7: defaults methods
    
    # 8: fields
    name = fields.Char(string='Description',)
    amount = fields.Float(string='Harga Jual')
    amount_subtotal = fields.Float(compute='_amount_line', string='Subtotal', digits='Account',store=True)
    type = fields.Selection([('sold','Sold'),('scrap','Scrap')],string="Type")
    nilai_penyusutan = fields.Float('Penyusutan Per Bln',compute='compute_asset_data')
    amount_depreciated = fields.Float('Akumulasi Penyusutan',compute='compute_asset_data')
    book_value = fields.Float('Nilai Buku',compute='compute_asset_data')
    nilai_asset = fields.Float('Harga Beli',compute='compute_asset_data')
    
    # 9: relation fields
    company_id = fields.Many2one('res.company',related='disposal_id.company_id',string='Branch')
    asset_id = fields.Many2one('account.asset.asset',string='Asset No',domain="[('company_id','=',company_id),('state','in',['open','close']),('category_id.type_assets','!=','asset_prepayments')]")
    tax_id =  fields.Many2many('account.tax', 'tw_disposal_asset_line_tax', 'tw_disposal_asset_line_id', 'tax_id', 'Taxes',domain=[('type_tax_use','=','sale')])
    disposal_id = fields.Many2one('tw.asset.disposal',string='Disposal No')
    category_id = fields.Many2one(related='asset_id.category_id',string='Category',store=True)
    product_id = fields.Many2one(related='asset_id.product_id',string='Product')
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    @api.depends('amount', 'tax_id')
    def _amount_line(self):
        for line in self:
            if not line.tax_id or line.disposal_id.type != 'sold':
                line.amount_subtotal = line.amount
                continue

            currency = line.disposal_id.company_id.currency_id

            taxes_res = line.tax_id.compute_all(
                price_unit=line.amount,
                currency=currency,
                quantity=1,
                product=line.product_id,
                partner=line.disposal_id.partner_id
            )

            line.amount_subtotal = taxes_res['total_excluded']

    @api.depends('asset_id')
    def compute_asset_data(self):
        for me in self:
            me.nilai_asset = 0
            me.nilai_penyusutan = 0
            me.amount_depreciated = 0
            me.book_value = 0
            if me.asset_id:
                me.nilai_asset = me.asset_id.value
                me.nilai_penyusutan = me.asset_id.value / (me.asset_id.method_number or 60)
                me.amount_depreciated = me.asset_id.value - (me.asset_id.salvage_value + me.asset_id.value_residual)
                me.book_value = me.asset_id.value_residual

    @api.onchange('asset_id')
    def change_asset(self):
        self.category_id = False
        self.product_id = False
        self.amount = 0
        self.tax_id = False
        if self.asset_id :
            self.category_id = self.asset_id.category_id.id
            self.product_id = self.asset_id.product_id.id
            if self.disposal_id.type == 'scrap' :
                self.amount = self.asset_id.real_purchase_value

    @api.onchange('tax_id')
    def change_taxes(self):
        if self.tax_id and self.disposal_id.type == 'scrap' :
            self.tax_id = [(6,0,[])]

    
     
    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        additional_params = self._get_tax_base_line_additional_params()
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            **additional_params,
        )

    def _get_tax_base_line_additional_params(self):
        self.ensure_one()
        return {
            'tax_ids': self.tax_id,
            'quantity': 1,
            'partner_id': self.disposal_id.partner_id,
            'currency_id': self.disposal_id.company_id.currency_id,
            'price_unit': self.amount,
        }


