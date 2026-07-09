# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class InheritTwDealerSaleOrderLine(models.Model):
    _inherit = "tw.dealer.sale.order.line"

    # 7: defaults methods
    def _get_domain_hutang_komisi(self):
        branch = self.order_id.company_id
        return [
            ('state', 'in', ('approved','confirm')),
            ('company_id', 'in', [branch.id, branch.parent_id.id] if branch.parent_id else [branch.id]),
            ('date_start', '<=', fields.Date.today()),
            ('date_end', '>=', fields.Date.today())
        ]

    # 8: fields
    commission_type = fields.Char('Commission Type')
    amount_commission = fields.Float('Amount Komisi',help='Amount yang di dapat diganti user jika tipe bukan fix')
    amount_commission_master = fields.Float('Amount Master',compute='_compute_commission_id',store=True, help='Amount dari master')
    amount_commission_pph = fields.Float('Amount (Include PPh)',compute='_compute_commission_amount',store=True, help='Amount perhitungan setelah PPH')
    
    # 9: relation fields
    commission_id = fields.Many2one(comodel_name='tw.commission', string="Hutang Komisi")
    commission_line_id = fields.Many2one(comodel_name='tw.commission.line', string="Hutang Komisi line", compute='_compute_commission_line_id')
    commission_tax_id = fields.Many2one(comodel_name='account.tax', string="Pajak Komisi", compute='_compute_commission_tax_id', store=True)
    available_commission_ids = fields.Many2many(comodel_name='tw.commission', string="Available Hutang Komisi", compute='_compute_available_commission_id')
    
    # 10: computed fields
    
    @api.onchange('commission_id')
    def _onchange_commission_id(self):
        if self.commission_id:
            self.amount_commission = self.commission_line_id.amount
        else:
            self.amount_commission = 0.0
    
    @api.depends('order_id.company_id')
    def _compute_available_commission_id(self):
        for line in self:
            available_commission = self.env['tw.commission'].search(self._get_domain_hutang_komisi())
            eligible_commission_line = available_commission.commission_line_ids.filtered(lambda x: x.product_template_id == line.product_id.product_tmpl_id)
            line.available_commission_ids = [(6, 0, eligible_commission_line.mapped('commission_id.id'))]

    @api.depends('commission_id', 'order_id.mediator_id')
    def _compute_commission_tax_id(self):
        for line in self:
            if line.commission_id:
                # ? Info terbaru, PPH 3% sudah tidak digunakan lagi, semuanya menggunakan yang 2,5%
                tax_based_on_npwp = int(self.env['ir.config_parameter'].sudo().get_param("tw_dealer_sale_order_commission.pph_tax_based_on_npwp",0))
                
                commission_tax_id = self.env.ref('tw_account.tw_account_tax_pph_npwp').id
                if not line.order_id.mediator_id.no_npwp and tax_based_on_npwp:
                    commission_tax_id = self.env.ref('tw_account.tw_account_tax_pph_non_npwp').id
                
                if not commission_tax_id:
                    raise Warning(_("Commission Tax tidak ditemukan! Hubungi administrator"))

                line.commission_tax_id = commission_tax_id
            else:
                line.commission_tax_id = False

    @api.depends('commission_id')
    def _compute_commission_line_id(self):
        for line in self:
            if line.commission_id:
                line_commision = line.commission_id.commission_line_ids.filtered(lambda x: x.product_template_id == line.product_id.product_tmpl_id)
                if not line_commision:
                    raise Warning(_("Commission %s untuk product %s tidak ditemukan!" % (line_commision.commission_id.name, line.product_id.name)))
                line.commission_line_id = line_commision.id
            else:
                line.commission_line_id = False

    @api.depends('commission_id','commission_line_id')
    def _compute_commission_id(self):
        for line in self:
            commission_line = line.commission_line_id

            if commission_line:
                if not line.product_id:
                    raise Warning(_("Anda harus memilih produk sebelum memasukkan komisi!"))
                
                line.commission_type = commission_line.commission_id.commission_type
                line.amount_commission_master = commission_line.amount
            else:
                line.commission_type = False
                line.amount_commission_master = 0.0
    
    @api.depends('amount_commission','commission_line_id')
    def _compute_commission_amount(self):
        for line in self:
            if line.commission_line_id:
                if line.commission_line_id.amount < line.amount_commission:
                    raise Warning(_("Amount komisi %s tidak boleh lebih besar dari master %s!" % (line.amount_commission, line.commission_line_id.amount)))
                divison = (100 + line.commission_tax_id.amount) / 100
                line.amount_commission_pph = line.amount_commission / divison
            else:
                line.amount_commission_pph = 0.0
            line.recompute_helper += 1


    # 11: constraints & sql constraints

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super().create(vals_list)
        return create

    def write(self, vals):
        write = super().write(vals)
        self._validate_hc()
        return write
    

    # 13: action methods
    
    # 14: private methods
    def _get_gp_additional_price(self):
        self.ensure_one()
        price = super()._get_gp_additional_price()
        price += self.amount_commission_pph
        return price

    def _validate_hc(self):
        for line in self:
            if line.commission_id and line.order_id.state not in ('sale', 'done'):
                hc = [line.amount_commission, line.amount_commission_master, line.amount_commission_pph]
                if not all(hc):
                    raise Warning('Amount Hutang Komisi Tidak Boleh nilai negatif atau 0!')