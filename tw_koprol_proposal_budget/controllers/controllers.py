# -*- coding: utf-8 -*-
# from odoo import http


# class TwKoprolBudget(http.Controller):
#     @http.route('/tw_koprol_budget/tw_koprol_budget', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tw_koprol_budget/tw_koprol_budget/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tw_koprol_budget.listing', {
#             'root': '/tw_koprol_budget/tw_koprol_budget',
#             'objects': http.request.env['tw_koprol_budget.tw_koprol_budget'].search([]),
#         })

#     @http.route('/tw_koprol_budget/tw_koprol_budget/objects/<model("tw_koprol_budget.tw_koprol_budget"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tw_koprol_budget.object', {
#             'object': obj
#         })

