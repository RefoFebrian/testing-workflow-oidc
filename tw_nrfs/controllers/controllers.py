# -*- coding: utf-8 -*-
# from odoo import http


# class TwNrfs(http.Controller):
#     @http.route('/tw_nrfs/tw_nrfs', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_nrfs/tw_nrfs/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_nrfs.listing', {
#             'root': '/tw_nrfs/tw_nrfs',
#             'objects': http.request.env['tw_nrfs.tw_nrfs'].search([]),
#         })

#     @http.route('/tw_nrfs/tw_nrfs/objects/<model("tw_nrfs.tw_nrfs"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_nrfs.object', {
#             'object': obj
#         })

