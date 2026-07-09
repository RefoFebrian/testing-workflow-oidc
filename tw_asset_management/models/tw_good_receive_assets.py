# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _


class TwGoodReceiveAssets(models.Model):
    _name = "tw.good.receive.assets"
    _description = "Good Receive Assets"

    price = fields.Float(string='Price')
    price_tax = fields.Float(string='Price Tax')
    receive_date = fields.Datetime(string='Receive Date')
    
    picking_id = fields.Many2one('tw.good.receive', string='Picking')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    asset_register_id = fields.Many2one('account.asset.asset',string='Asset')
    
    