# -*- coding: utf-8 -*-
# from odoo import http


# class TwPricelistPurchaseOrder(http.Controller):
#     @http.route('/tw_pricelist_purchase_order/tw_pricelist_purchase_order', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_pricelist_purchase_order/tw_pricelist_purchase_order/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_pricelist_purchase_order.listing', {
#             'root': '/tw_pricelist_purchase_order/tw_pricelist_purchase_order',
#             'objects': http.request.env['tw_pricelist_purchase_order.tw_pricelist_purchase_order'].search([]),
#         })

#     @http.route('/tw_pricelist_purchase_order/tw_pricelist_purchase_order/objects/<model("tw_pricelist_purchase_order.tw_pricelist_purchase_order"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_pricelist_purchase_order.object', {
#             'object': obj
#         })

