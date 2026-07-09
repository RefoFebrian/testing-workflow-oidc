# -*- coding: utf-8 -*-
# from odoo import http


# class TwPurchaseOrder(http.Controller):
#     @http.route('/tw_purchase_order/tw_purchase_order', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_purchase_order/tw_purchase_order/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_purchase_order.listing', {
#             'root': '/tw_purchase_order/tw_purchase_order',
#             'objects': http.request.env['tw_purchase_order.tw_purchase_order'].search([]),
#         })

#     @http.route('/tw_purchase_order/tw_purchase_order/objects/<model("tw_purchase_order.tw_purchase_order"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_purchase_order.object', {
#             'object': obj
#         })

