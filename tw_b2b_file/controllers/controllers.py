# -*- coding: utf-8 -*-
# from odoo import http


# class TwB2bFile(http.Controller):
#     @http.route('/tw_b2b_file/tw_b2b_file', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_b2b_file/tw_b2b_file/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_b2b_file.listing', {
#             'root': '/tw_b2b_file/tw_b2b_file',
#             'objects': http.request.env['tw_b2b_file.tw_b2b_file'].search([]),
#         })

#     @http.route('/tw_b2b_file/tw_b2b_file/objects/<model("tw_b2b_file.tw_b2b_file"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_b2b_file.object', {
#             'object': obj
#         })

