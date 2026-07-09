# -*- coding: utf-8 -*-
# from odoo import http


# class TwIncentiveApproval(http.Controller):
#     @http.route('/tw_incentive_approval/tw_incentive_approval', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_incentive_approval/tw_incentive_approval/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_incentive_approval.listing', {
#             'root': '/tw_incentive_approval/tw_incentive_approval',
#             'objects': http.request.env['tw_incentive_approval.tw_incentive_approval'].search([]),
#         })

#     @http.route('/tw_incentive_approval/tw_incentive_approval/objects/<model("tw_incentive_approval.tw_incentive_approval"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_incentive_approval.object', {
#             'object': obj
#         })

