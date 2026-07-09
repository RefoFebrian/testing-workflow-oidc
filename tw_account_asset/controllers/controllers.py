# -*- coding: utf-8 -*-
# from odoo import http


# class TwAccountAsset(http.Controller):
#     @http.route('/tw_account_asset/tw_account_asset', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_account_asset/tw_account_asset/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_account_asset.listing', {
#             'root': '/tw_account_asset/tw_account_asset',
#             'objects': http.request.env['tw_account_asset.tw_account_asset'].search([]),
#         })

#     @http.route('/tw_account_asset/tw_account_asset/objects/<model("tw_account_asset.tw_account_asset"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_account_asset.object', {
#             'object': obj
#         })

