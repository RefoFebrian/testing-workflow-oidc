# -*- coding: utf-8 -*-
# from odoo import http


# class TwAssetManagement(http.Controller):
#     @http.route('/tw_asset_management/tw_asset_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_asset_management/tw_asset_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_asset_management.listing', {
#             'root': '/tw_asset_management/tw_asset_management',
#             'objects': http.request.env['tw_asset_management.tw_asset_management'].search([]),
#         })

#     @http.route('/tw_asset_management/tw_asset_management/objects/<model("tw_asset_management.tw_asset_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_asset_management.object', {
#             'object': obj
#         })

