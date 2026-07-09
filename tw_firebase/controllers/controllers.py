# -*- coding: utf-8 -*-
# from odoo import http


# class TwFirebase(http.Controller):
#     @http.route('/tw_firebase/tw_firebase', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_firebase/tw_firebase/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_firebase.listing', {
#             'root': '/tw_firebase/tw_firebase',
#             'objects': http.request.env['tw_firebase.tw_firebase'].search([]),
#         })

#     @http.route('/tw_firebase/tw_firebase/objects/<model("tw_firebase.tw_firebase"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_firebase.object', {
#             'object': obj
#         })

