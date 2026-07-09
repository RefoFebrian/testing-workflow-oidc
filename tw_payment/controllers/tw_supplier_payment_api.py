#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import functools
import werkzeug.wrappers
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response 
from odoo.addons.rest_api.controllers.main import check_valid_token, valid_response
# 3:  imports of odoo
import odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

class ControllerREST(http.Controller):

    @http.route('/api/tw_payment/v1/post_create_supplier_payment/', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_create_supplier_payment(self, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        branch_code = post.get('branch_code')
        memo = post.get('memo')
        division = post.get('division')
        date_payment = post.get('date') or post.get('payment_date') or fields.Date.today()
        payment_request_name = (
            post.get('payment_request_name')
            or post.get('payment_request_number')
            or post.get('payment_request')
        )
        partner_code = post.get('partner_code')

        try:
            amount = float(post.get('amount') or post.get('actual_amount_total') or 0.0)
        except (TypeError, ValueError):
            info = "Invalid amount supplier payment: %s" % (post.get('amount') or post.get('actual_amount_total'))
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        branch = request.env['res.company'].sudo().search([('code', '=', branch_code)], limit=1)
        if not branch:
            info = "invalid data for kode branch [%s]" % (branch_code)
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        if not payment_request_name:
            info = "Payment Request number is required!"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        payment_request = request.env['tw.payment.request'].sudo().search([
            ('name', '=', payment_request_name),
            ('company_id', '=', branch.id),
        ], limit=1)

        if payment_request:
            amount = amount or payment_request.amount or payment_request.amount_total
            division = division or payment_request.division
            memo = memo or payment_request.name

        if amount <= 0.0:
            info = "Amount supplier payment harus lebih dari 0!"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        if post.get('partner_id'):
            partner = request.env['res.partner'].sudo().browse(int(post.get('partner_id')))
        elif partner_code:
            partner = request.env['res.partner'].sudo().search([('code', '=', partner_code)], limit=1)
        elif payment_request:
            partner = payment_request.partner_id
        else:
            partner = request.env['res.partner'].sudo().search([
                ('code', '=', 'UMUM-MD'),
                ('name', '=', 'UMUM'),
            ], limit=1)
        if not partner:
            info = "Partner supplier payment tidak ditemukan !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        journal_domain = request.env['account.journal'].sudo()._check_company_domain(branch)
        journal_domain.append(('type', 'in', ['bank', 'cash', 'credit']))
        journal = request.env['account.journal'].sudo().search(journal_domain, limit=1)
        if not journal:
            info = "Journal supplier payment cabang [%s] tidak ditemukan !" % (branch_code)
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        payment_date = fields.Date.to_date(date_payment)
        liquidity_amount_currency = -amount
        liquidity_balance = branch.currency_id._convert(
            liquidity_amount_currency,
            branch.currency_id,
            branch,
            payment_date,
        )
        account = journal.default_debit_account_id if liquidity_balance > 0.0 else journal.default_credit_account_id
        account_id = account.id if account else journal.default_account_id.id
        if not account_id:
            info = "Konfigurasi jurnal account cabang belum dibuat, silahkan setting dulu !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        move_line = request.env['account.move.line'].sudo().search([
            ('ref', '=', payment_request_name),
            ('account_id.account_type', '=', 'liability_payable'),
            ('company_id', '=', branch.id),
            ('amount_residual', '!=', 0),
        ], limit=1)
        if not move_line:
            info = "Payable line Payment Request [%s] tidak ditemukan !" % (payment_request_name)
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        line_type = 'dr' if move_line.credit else 'cr'
        currency_id = journal.company_id.currency_id.id

        if move_line.currency_id and currency_id == move_line.currency_id.id:
            amount_original = abs(move_line.amount_currency)
            amount_unreconciled = abs(move_line.amount_residual_currency)
        else:
            amount_original = move_line.company_id.currency_id._convert(
                move_line.credit or move_line.debit or 0.0,
                branch.currency_id,
                branch,
                payment_date,
            )
            amount_unreconciled = move_line.company_id.currency_id._convert(
                abs(move_line.amount_residual),
                branch.currency_id,
                branch,
                payment_date,
            )

        vals = {
            'company_id': branch.id,
            'partner_id': partner.id,
            'division': division,
            'type': 'supplier_payment',
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'amount': amount,
            'date': payment_date,
            'journal_id': journal.id,
            'account_id': account_id,
            'currency_id': currency_id,
            'memo': 'Supplier Payment Perjalanan Dinas - ' + str(memo or payment_request_name),
            'line_dr_ids': [
                (0, 0, {
                    'move_line_id': move_line.id,
                    'name': move_line.move_id.name,
                    'amount_original': amount_original,
                    'amount': amount_unreconciled,
                    'date_original': move_line.date,
                    'date_due': move_line.date_maturity,
                    'amount_unreconciled': amount_unreconciled,
                    'account_id': move_line.account_id.id,
                    'type': line_type,
                    'is_reconciled': True,
                    'currency_id': move_line.currency_id.id or move_line.company_id.currency_id.id,
                })
            ]
        }

        try:
            supplier_payment = request.env['tw.account.payment'].sudo().with_company(branch).create(vals)
        except Exception as err:
            request._cr.rollback()
            info = "Gagal Create Supplier Payment : %s" % (err)
            error = 'Bad Request'
            _logger.error(err)
            return invalid_response(400, error, info)

        name = "Success Create Supplier Payment TEDS: '%s'" % (supplier_payment.name or supplier_payment.id)
        return valid_response(status=200, data=name)
