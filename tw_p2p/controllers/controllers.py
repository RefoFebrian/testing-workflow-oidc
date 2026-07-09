# -*- coding: utf-8 -*-
# from odoo import http


# class TwP2p(http.Controller):
#     @http.route('/tw_p2p/tw_p2p', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_p2p/tw_p2p/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_p2p.listing', {
#             'root': '/tw_p2p/tw_p2p',
#             'objects': http.request.env['tw_p2p.tw_p2p'].search([]),
#         })

#     @http.route('/tw_p2p/tw_p2p/objects/<model("tw_p2p.tw_p2p"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_p2p.object', {
#             'object': obj
#         })

