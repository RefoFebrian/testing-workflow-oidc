# -*- coding: utf-8 -*-
# from odoo import http


# class TwPricelistBbn(http.Controller):
#     @http.route('/tw_pricelist_bbn/tw_pricelist_bbn', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_pricelist_bbn/tw_pricelist_bbn/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_pricelist_bbn.listing', {
#             'root': '/tw_pricelist_bbn/tw_pricelist_bbn',
#             'objects': http.request.env['tw_pricelist_bbn.tw_pricelist_bbn'].search([]),
#         })

#     @http.route('/tw_pricelist_bbn/tw_pricelist_bbn/objects/<model("tw_pricelist_bbn.tw_pricelist_bbn"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_pricelist_bbn.object', {
#             'object': obj
#         })

