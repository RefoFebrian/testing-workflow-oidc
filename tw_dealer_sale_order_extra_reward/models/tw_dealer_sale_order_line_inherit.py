# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwDealerSaleOrderLineInherit(models.Model):
    _inherit = "tw.dealer.sale.order.line"

    # 7: defaults methods

    # 8: fields
    extra_reward_value = fields.Float('Extra Reward exc. PPh 21')
    amount_extra_reward = fields.Float('Total Extra Reward', help='Total Extra Reward setelah di tambah PPh 21')

    # 9: relation fields
    extra_reward_tax_id = fields.Many2one(comodel_name='account.tax', string="Extra Reward Tax", compute='_compute_extra_reward_tax_id', store=True)
    extra_reward_partner_id = fields.Many2one('res.partner', 'Partner', domain=[('category_id.name', '=', 'Customer')])
    

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('partner_stnk_id')
    def _onchange_partner_stnk_id(self):
        for line in self:
            line.extra_reward_partner_id = line.partner_stnk_id
    
    @api.onchange('extra_reward_value')
    def _onchange_extra_reward_value(self):
        self.amount_extra_reward = 0
        if self.extra_reward_value:

            divison = (100 + self.extra_reward_tax_id.amount) / 100
            self.amount_extra_reward = self.extra_reward_value / divison

    @api.depends('order_id.mediator_id','extra_reward_value')
    def _compute_extra_reward_tax_id(self):
        for line in self:
            # ? Info terbaru, PPH 3% sudah tidak digunakan lagi, semuanya menggunakan yang 2,5%
            tax_based_on_npwp = int(self.env['ir.config_parameter'].sudo().get_param("tw_dealer_sale_order_extra_reward.pph_tax_based_on_npwp",0))
            
            extra_reward_tax_id = self.env.ref('tw_account.tw_account_tax_pph_npwp').id
            if not line.order_id.mediator_id.no_npwp and tax_based_on_npwp:
                extra_reward_tax_id = self.env.ref('tw_account.tw_account_tax_pph_non_npwp').id
            
            if not extra_reward_tax_id:
                raise Warning(_("Extra_reward Tax tidak ditemukan! hubungi administrator"))
            line.extra_reward_tax_id = extra_reward_tax_id

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('partner_stnk_id'):
                vals['extra_reward_partner_id'] = vals['partner_stnk_id']
        create = super().create(vals_list)
        return create

    def write(self, vals):
        #For assign extra reward partner 
        for line in self:
            if line.state == 'draft':
                partner_stnk = vals.get('partner_stnk_id', line.partner_stnk_id.id)
                if not line.extra_reward_partner_id and not vals.get('extra_reward_partner_id'):
                    vals['extra_reward_partner_id'] = partner_stnk
        
        # Force to recompute amount extra reward if onchange_amount_extra_reward is not working
        extra_reward_value = vals.get('extra_reward_value', self.extra_reward_value)
        amount_extra_reward = vals.get('amount_extra_reward', self.amount_extra_reward)
        if extra_reward_value and not amount_extra_reward:
            divison = (100 + self.extra_reward_tax_id.amount) / 100
            vals['amount_extra_reward'] = extra_reward_value / divison
            
        write = super().write(vals)
        
        return write

    # 13: action methods

    # 14: private methods
    def _get_gp_additional_price(self):
        self.ensure_one()
        price = super()._get_gp_additional_price()
        price += self.amount_extra_reward
        return price