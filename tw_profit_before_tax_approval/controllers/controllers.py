# -*- coding: utf-8 -*-
# from odoo import http


# class TwProfitBeforeTaxApproval(http.Controller):
#     @http.route('/tw_profit_before_tax_approval/tw_profit_before_tax_approval', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_profit_before_tax_approval/tw_profit_before_tax_approval/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_profit_before_tax_approval.listing', {
#             'root': '/tw_profit_before_tax_approval/tw_profit_before_tax_approval',
#             'objects': http.request.env['tw_profit_before_tax_approval.tw_profit_before_tax_approval'].search([]),
#         })

#     @http.route('/tw_profit_before_tax_approval/tw_profit_before_tax_approval/objects/<model("tw_profit_before_tax_approval.tw_profit_before_tax_approval"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_profit_before_tax_approval.object', {
#             'object': obj
#         })

