# -*- coding: utf-8 -*-
# from odoo import http


# class TwMrp(http.Controller):
#     @http.route('/tw_mrp/tw_mrp', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_mrp/tw_mrp/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_mrp.listing', {
#             'root': '/tw_mrp/tw_mrp',
#             'objects': http.request.env['tw_mrp.tw_mrp'].search([]),
#         })

#     @http.route('/tw_mrp/tw_mrp/objects/<model("tw_mrp.tw_mrp"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_mrp.object', {
#             'object': obj
#         })

