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


class InheritDealerSaleOrder(models.Model):
    _inherit = "tw.dealer.sale.order"

    cdb_stnk_id = fields.Many2one('tw.partner.cdb', string='CDB Customer')

    def action_confirm(self):
        """
        Override the confirm action to create CDB data when order is confirmed
        """
        partner_cdb_obj = self.sudo().create_cdb_data()
        res = super(InheritDealerSaleOrder, self).action_confirm()
        self.cdb_stnk_id = partner_cdb_obj.id

        lot_values = []
        lot_obj = self.env['stock.lot']
        for line in self.order_line:
            if line.lot_id:
                continue
                # TODO: active again if dealer_sale_order_id is added to stock.lot
                # lot_values = {
                #     'dealer_sale_order_id': partner_cdb_obj.id
                # }
                # lot_obj.browse(line.lot_id.id)
        
        return res

    def create_cdb_data(self):
        """
        Create CDB (Customer Database) records from dealer sale order data.
        This method is typically called when a sale order is confirmed.
        """
        for order in self.filtered(lambda o: o.partner_id):
            # Check if CDB record already exists for this partner and lot
            order_line_objs = order.order_line.filtered(lambda l: l.item_type == 'main')
            for line in order_line_objs:
                customer_stnk = order.partner_id
                # Prepare CDB values from partner and order data
                cdb_vals = order._prepare_partner_cdb()
                
                # Create CDB record
                cdb_record = customer_stnk.sync_partner_to_cdb(**cdb_vals)
            
                # Link the CDB record to the partner
                customer_stnk.write({
                    'cdb_partner_ids': [(4, cdb_record.id)]
                })
            
        return cdb_record