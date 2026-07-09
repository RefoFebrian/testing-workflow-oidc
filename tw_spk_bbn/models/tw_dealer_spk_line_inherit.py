# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class DealerSPKLineBBN(models.Model):
    _inherit = "tw.dealer.spk.line"

    # 7: defaults methods
    
    # 8: fields
    # is_bbn = fields.Boolean(string='BBN?')

    # 9: relation fields

    # 10: constraints & sql constraints
    # @api.constrains('spk_id', 'is_bbn')
    # def _check_bbn(self):
    #     for record in self:
    #         if record.spk_id.finco_id and not record.is_bbn:
    #             raise ValidationError(_("BBN must be checked if a Finco is selected."))

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods

    # 14: private methods
    def _prepare_dealer_sale_order_line_vals(self):
        vals_line = super()._prepare_dealer_sale_order_line_vals()

        spk_obj = self.spk_id
        branch_setting_obj = spk_obj.company_id.branch_setting_id
        account_conf = branch_setting_obj.account_setting_id
        price_bbn_purchase = price_bbn_notice = price_bbn_process = 0.0
        price_bbn_serv = price_bbn_serv_area = price_bbn_capital_fee = 0.0
        default_birojasa = False

        accrue_expedition = account_conf.accrue_expedition if account_conf.is_accrue_expedition else 0
        accrue_bbn_process = 0
        if self.partner_stnk_id:
            stnk = self.partner_stnk_id
        else:
            stnk = spk_obj.lead_id.partner_id

        if self.is_bbn:
            accrue_bbn_process = account_conf.accrue_bbn_process if account_conf.is_accrue_proses_bbn else 0
            city = stnk.city_id

            if not city:
                raise Warning("Customer STNK address is incomplete!")
               
            if not branch_setting_obj.birojasa_setting_ids:
                raise Warning(f'Birojasa setting for branch "{spk_obj.company_id.name}" is not set, please set it first')

            default_birojasa_setting = branch_setting_obj.birojasa_setting_ids.filtered(lambda x: x.default)
            default_birojasa = default_birojasa_setting.biro_jasa_id

            if default_birojasa:
                pricelist_sales_bbn = spk_obj._get_pricelist_sales_bbn(self.plate_id)
                price_bbn = pricelist_sales_bbn.with_company(spk_obj.company_id.id)._price_get(self.product_id, self.product_qty)[pricelist_sales_bbn.id]
                pricelist_purhcase_bbn = self.env['product.pricelist']._get_bbn_purchase_pricelist(default_birojasa, spk_obj.company_id)
                pricelist_item = pricelist_purhcase_bbn._get_applicable_rules(self.product_id, spk_obj.date_order, city_id=city.id)
                if not pricelist_item:
                    raise Warning(_(f"No applicable rules for product {self.product_id.name} and city {city.name} in {pricelist_purhcase_bbn.name}"))

                price_bbn_purchase = pricelist_item.fixed_price
                price_bbn_notice = pricelist_item.notice_price
                price_bbn_process = pricelist_item.process_price
                price_bbn_serv = pricelist_item.serv_price
                price_bbn_serv_area = pricelist_item.serv_area_price
                price_bbn_capital_fee = pricelist_item.capital_fee_price

                vals_line.update({
                    'is_bbn': self.is_bbn,
                    'biro_jasa_id': default_birojasa.id if default_birojasa else False,
                    'accrue_expedition': accrue_expedition or 0.0,
                    'accrue_bbn_process': accrue_bbn_process or 0.0,
                    'bbn_amount': price_bbn,
                    'bbn_purchase_amount': price_bbn_purchase,
                    'bbn_notice_amount': price_bbn_notice,
                    'bbn_process_amount': price_bbn_process,
                    'bbn_serv_amount': price_bbn_serv,
                    'bbn_serv_area_amount': price_bbn_serv_area,
                    'bbn_capital_fee_amount': price_bbn_capital_fee,
                })

        return vals_line

