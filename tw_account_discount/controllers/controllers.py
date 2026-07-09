# -*- coding: utf-8 -*-
# from odoo import http


# class TwAccountDiscount(http.Controller):
#     @http.route('/tw_account_discount/tw_account_discount', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_account_discount/tw_account_discount/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_account_discount.listing', {
#             'root': '/tw_account_discount/tw_account_discount',
#             'objects': http.request.env['tw_account_discount.tw_account_discount'].search([]),
#         })

#     @http.route('/tw_account_discount/tw_account_discount/objects/<model("tw_account_discount.tw_account_discount"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_account_discount.object', {
#             'object': obj
#         })

