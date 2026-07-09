# -*- coding: utf-8 -*-
# from odoo import http


# class TwBankTransferCancel(http.Controller):
#     @http.route('/tw_bank_transfer_cancel/tw_bank_transfer_cancel', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_bank_transfer_cancel/tw_bank_transfer_cancel/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_bank_transfer_cancel.listing', {
#             'root': '/tw_bank_transfer_cancel/tw_bank_transfer_cancel',
#             'objects': http.request.env['tw_bank_transfer_cancel.tw_bank_transfer_cancel'].search([]),
#         })

#     @http.route('/tw_bank_transfer_cancel/tw_bank_transfer_cancel/objects/<model("tw_bank_transfer_cancel.tw_bank_transfer_cancel"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_bank_transfer_cancel.object', {
#             'object': obj
#         })

