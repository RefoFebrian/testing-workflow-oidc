# -*- coding: utf-8 -*-
# from odoo import http


# class TwAccountStockInbound(http.Controller):
#     @http.route('/tw_account_stock_inbound/tw_account_stock_inbound', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_account_stock_inbound/tw_account_stock_inbound/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_account_stock_inbound.listing', {
#             'root': '/tw_account_stock_inbound/tw_account_stock_inbound',
#             'objects': http.request.env['tw_account_stock_inbound.tw_account_stock_inbound'].search([]),
#         })

#     @http.route('/tw_account_stock_inbound/tw_account_stock_inbound/objects/<model("tw_account_stock_inbound.tw_account_stock_inbound"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_account_stock_inbound.object', {
#             'object': obj
#         })

