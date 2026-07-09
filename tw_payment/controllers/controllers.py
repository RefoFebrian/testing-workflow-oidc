# -*- coding: utf-8 -*-
# from odoo import http


# class TwPayment(http.Controller):
#     @http.route('/tw_payment/tw_payment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_payment/tw_payment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_payment.listing', {
#             'root': '/tw_payment/tw_payment',
#             'objects': http.request.env['tw_payment.tw_payment'].search([]),
#         })

#     @http.route('/tw_payment/tw_payment/objects/<model("tw_payment.tw_payment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_payment.object', {
#             'object': obj
#         })

