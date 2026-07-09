# -*- coding: utf-8 -*-
# from odoo import http


# class TwIncentive(http.Controller):
#     @http.route('/tw_incentive/tw_incentive', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_incentive/tw_incentive/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_incentive.listing', {
#             'root': '/tw_incentive/tw_incentive',
#             'objects': http.request.env['tw_incentive.tw_incentive'].search([]),
#         })

#     @http.route('/tw_incentive/tw_incentive/objects/<model("tw_incentive.tw_incentive"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_incentive.object', {
#             'object': obj
#         })

