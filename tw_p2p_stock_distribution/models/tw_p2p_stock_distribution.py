# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime


# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)
# 6: Import of unknown third party lib


class TwP2pStockDistribution(models.Model):
    _inherit = "tw.p2p.purchase.order"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    stock_distribution_id = fields.Many2one('tw.stock.distribution',string='Stock Distribution')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods    
    def confirm_order(self):    
        super(TwP2pStockDistribution,self).confirm_order()
        main_dealer_code = self.env['res.company'].get_default_main_dealer_code()
        distribution_obj = False
        vals_confirm = {}
        branch_sender = self.env['res.company'].suspend_security().search([('partner_id','=',self.supplier_id.id)])
        if branch_sender and branch_sender.branch_type_id.value == 'MD':
            distribution_obj = self.env['tw.stock.distribution'].sudo().search([('origin','=',self.name)])
            if distribution_obj:
                raise Warning("SD Sudah terbentuk dengan nomor '%s'!"%(distribution_obj.name))
            else:
                distribution_obj = self.action_create_distribution()
                distribution_obj.stock_distribution_ids.product_id_change()
                vals_confirm['stock_distribution_id'] = distribution_obj.id
        
        return self.write(vals_confirm)

    def action_create_distribution(self):
        type = self.purchase_order_type_id
        start_date = type.get_date(type.start_date_id.value)
        end_date = type.get_date(type.end_date_id.value)
        company_obj = self.env['res.company'].sudo().search([('partner_id', '=', self.dealer_id.id)], limit=1)
        if not company_obj :
            raise Warning("Branch untuk Dealer tidak ditemukan")
            
        branch_sender_id=company_obj.id
        branch_config = company_obj.branch_setting_id
        total_qty = 0.0   
        if self.type_name == 'Fix'   :                                          
            for line in self.purchase_line_ids :
                  total_qty += line.fix_qty 
            if total_qty < 1 :
                    raise Warning("Total Fix Qty harus lebih besar dari 0")
        elif self.type_name == 'Additional'   :                                          
            for line in self.additional_line_ids :
                  total_qty += line.fix_qty 
            if total_qty < 1 :
                    raise Warning("Total Fix Qty harus lebih besar dari 0")
                        
        distribution_vals = {
                             'company_id': branch_sender_id  ,
                             'requester_id': self.dealer_id.id ,
                             'division' : self.division,
                             'origin' : self.name,
                             'model_name': self._name, #function to get model name and view smart button to open record origin
                             'purchase_order_type_id': self.purchase_order_type_id.id,
                             'date': self.date,
                             'start_date': start_date,
                             'end_date': end_date,
                             'description': self.description,
                             'state': 'draft',
                             }
        
        
        distribution_line_vals = []
        if self.type_name == 'Fix' :
            for line in self.purchase_line_ids :
                if line.fix_qty > 0 :
                    price = line.product_id.standard_price
                    if self.division == 'Unit' :

                        if branch_config.pricelist_purchase_unit_id.id:
                            price=self._get_price_unit(branch_config.pricelist_purchase_unit_id,line.product_id)
                        if not price :
                            raise Warning("Product %s tidak ada dalam pricelist beli unit")%(line.product_id.name)  
                    elif self.division == 'Sparepart' :
                        if branch_config.pricelist_purchase_sparepart_id.id:
                            price=self._get_price_unit(branch_config.pricelist_purchase_sparepart_id,line.product_id)
                        if not price :
                            raise Warning("Product %s tidak ada dalam pricelist beli part"%(line.product_id.name))
                    distribution_line_vals.append([0,False,
                                            {
                                              'product_id': line.product_id.id,
                                              'description': line.product_id.description,
                                              'requested_qty': line.fix_qty,
                                              'approved_qty':line.fix_qty,
                                              'qty': 0,
                                              'supply_qty': 0,
                                              'price': price,
                                              }])
        elif self.type_name == 'Additional' :
            for line in self.additional_line_ids :
                if line.fix_qty > 0 :
                    price = line.product_id.standard_price
                    if self.division == 'Unit' :
                        if branch_config.pricelist_purchase_unit_id:
                            price=self._get_price_unit(branch_config.pricelist_purchase_unit_id,line.product_id)
                        if not price :
                            raise Warning("Product %s tidak ada dalam pricelist beli unit")%(line.product_id.name)  
                    elif self.division == 'Sparepart' :
                        if branch_config.pricelist_purchase_sparepart_id:
                            price=self._get_price_unit(branch_config.pricelist_purchase_sparepart_id,line.product_id)
                        if not price :
                            raise Warning("Product %s tidak ada dalam pricelist beli part"%(line.product_id.name))
                                                                
                    distribution_line_vals.append([0,False,
                                            {
                                              'product_id': line.product_id.id,
                                              'description': line.product_id.description,
                                              'requested_qty': line.fix_qty,
                                              'approved_qty':line.fix_qty,
                                              'qty': 0,
                                              'supply_qty': 0,
                                              'price': price,
                                              }])
                    
        distribution_vals['stock_distribution_ids'] = distribution_line_vals
        distribution_id = self.env['tw.stock.distribution'].sudo().create(distribution_vals)
        return distribution_id

    def action_view_sd(self,context=None):  
        sd_ids = self.env['tw.stock.distribution'].suspend_security().search([('origin','=',self.name)]).id
        return {
            'name': 'Stock Distribution',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.stock.distribution',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': sd_ids
            }
        


    