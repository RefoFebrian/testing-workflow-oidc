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
    def _get_customer_payment_invoice(self, invoice_id):
        return request.env['account.move'].sudo().search([
            ('id', '=', invoice_id),
            ('move_type', '=', 'out_invoice'),
        ], limit=1)

    def _get_customer_payment_work_order(self, invoice):
        work_order = invoice.invoice_line_ids.mapped('work_order_line_ids.order_id')[:1]
        if work_order:
            return work_order
        if invoice.invoice_origin:
            return request.env['tw.work.order'].sudo().search([('name', '=', invoice.invoice_origin)], limit=1)
        return request.env['tw.work.order']

    def _get_customer_payment_move_line(self, invoice):
        move_line = invoice.line_ids.filtered(
            lambda line: (
                line.display_type == 'payment_term'
                and line.account_id.account_type == 'asset_receivable'
                and not line.reconciled
                and not line.full_reconcile_id
            )
        )[:1]
        if move_line:
            return move_line
        return request.env['account.move.line'].sudo().search([
            ('move_id', '=', invoice.id),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('debit', '>', 0),
            ('reconciled', '=', False),
            ('full_reconcile_id', '=', False),
        ], limit=1)

    def _get_customer_payment_branch_setting(self, invoice):
        branch_setting = invoice.company_id.branch_setting_id
        if branch_setting:
            return branch_setting
        return request.env['tw.branch.setting'].sudo().search([('company_id', '=', invoice.company_id.id)], limit=1)

    def _get_customer_payment_method_values(self, pembayaran, invoice, work_order, branch_setting):
        journal = False
        amount = 0.0
        name = ''
        account_setting = branch_setting.account_setting_id

        if pembayaran == 'voucher service':
            voucher = getattr(work_order, 'voucher_service_id', False)
            if getattr(work_order, 'is_voucher_service', False) and voucher and hasattr(voucher, 'action_done'):
                voucher.sudo().action_done()
            amount = getattr(work_order, 'nominal_voucher_terpakai', 0.0) or 0.0
            journal = getattr(account_setting, 'wo_customer_payment_voucher_journal_id', False) or account_setting.wo_customer_payment_journal_id
            name = 'Pencairan Voucher Service'
        elif pembayaran == 'edc':
            amount = invoice.amount_residual or invoice.amount_total
            journal = getattr(account_setting, 'wo_customer_payment_edc_journal_id', False) or account_setting.wo_customer_payment_journal_id
            name = 'Pembayaran melalui Mesin EDC'
        elif pembayaran == 'payment gateway':
            amount = invoice.amount_residual or invoice.amount_total
            journal = account_setting.wo_customer_payment_journal_id
            name = 'Pembayaran melalui Mesin'

        return journal, amount, name

    def _get_inbound_manual_payment_method(self):
        payment_method = request.env['account.payment.method'].sudo().search([
            ('payment_type', '=', 'inbound'),
            ('name', '=ilike', '%manual payment%'),
        ], limit=1)
        if not payment_method:
            payment_method = request.env['account.payment.method'].sudo().search([
                ('payment_type', '=', 'inbound'),
                ('code', '=', 'manual'),
            ], limit=1)
        return payment_method

    @http.route('/api/tw_payment/v1/post_create_customer_payment/', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_create_customer_payment(self, **post):
        if request.httprequest.content_type not in ('application/json', 'application/json; charset=utf-8'):
            error = "Content type harus salah satu dari: application/json atau application/json; charset=utf-8. Saat ini: %s" % request.httprequest.content_type
            return {
                'message': error,
                'status': 0,
            }

        post = json.loads(request.httprequest.get_data(as_text=True))
        invoice_ids = post.get('invoice_ids') or []
        if not invoice_ids:
            info = "Parameter invoice_ids tidak boleh kosong!"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        name_customer_payment = []
        invoices = []
        last_pembayaran = ''

        for data in invoice_ids:
            invoice_id = data.get('id')
            order_id = data.get('order_id')
            pembayaran = (data.get('pembayaran') or '').lower()
            last_pembayaran = pembayaran

            if not order_id:
                info = "Order ID invalid data, data not found"
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)

            allowed_pembayaran = ['voucher service', 'edc', 'payment gateway']
            if pembayaran not in allowed_pembayaran:
                info = "Metode pembayaran [%s] tidak valid, harus salah satu dari %s" % (pembayaran or '-', ", ".join(allowed_pembayaran))
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)

            invoice_obj = self._get_customer_payment_invoice(invoice_id)
            if not invoice_obj:
                info = "Invoice invalid data for id [%s] , data not found" % (invoice_id)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)

            wo_obj = self._get_customer_payment_work_order(invoice_obj)
            if not wo_obj:
                info = "WO invalid data for invoice [%s] , data not found" % (invoice_obj.name)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)

            move_line = self._get_customer_payment_move_line(invoice_obj)
            if not move_line:
                info = "Move line piutang untuk invoice [%s] tidak ditemukan" % (invoice_obj.name)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)

            branch_setting = self._get_customer_payment_branch_setting(invoice_obj)
            if not branch_setting:
                info = "Konfigurasi cabang %s belum dibuat, silahkan setting dulu!" % (invoice_obj.company_id.name)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
            if not branch_setting.account_setting_id:
                info = "Account setting tidak ditemukan untuk branch [%s]" % (invoice_obj.company_id.name)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)

            journal_obj, amount, name_pembayaran = self._get_customer_payment_method_values(
                pembayaran, invoice_obj, wo_obj, branch_setting
            )

            if not journal_obj:
                info = "Branch %s belum setting journal untuk pembayaran %s" % (invoice_obj.company_id.name, pembayaran)
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
            if not amount or amount <= 0:
                info = "Nominal pembayaran harus lebih dari 0"
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)

            payment_method_obj = self._get_inbound_manual_payment_method()
            if not payment_method_obj:
                info = "Payment Method 'Manual Payment' untuk inbound tidak ditemukan!"
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)

            vals = {
                'company_id': invoice_obj.company_id.id,
                'beneficiary_company_id': invoice_obj.company_id.id,
                'division': 'Sparepart',
                'payment_type': 'inbound',
                'type': 'customer_payment',
                'partner_type': 'customer',
                'partner_id': invoice_obj.partner_id.id,
                'amount': amount,
                'journal_id': journal_obj.id,
                'memo': name_pembayaran,
                'narration': name_pembayaran,
                'currency_id': invoice_obj.currency_id.id,
                'account_id': move_line.account_id.id,
                'payment_method_id': payment_method_obj.id,
                'account_number': journal_obj.name,
                'account_holder': invoice_obj.partner_id.name,
                'line_cr_ids': [(0, 0, {
                    'move_line_id': move_line.id,
                    'account_id': move_line.account_id.id,
                    'name': name_pembayaran,
                    'type': 'cr',
                    'amount': amount,
                    'amount_untaxed': amount,
                    'amount_unreconciled': abs(move_line.amount_residual_currency or move_line.amount_residual),
                    'is_reconciled': True,
                    'currency_id': move_line.currency_id.id or move_line.company_id.currency_id.id,
                })],
            }
            vals = {
                key: value
                for key, value in vals.items()
                if key in request.env['tw.account.payment']._fields
            }

            try:
                create_customer_payment = request.env['tw.account.payment'].sudo().with_company(invoice_obj.company_id).create(vals)
                create_customer_payment.sudo().action_post()
                if pembayaran != 'voucher service':
                    wo_obj.sudo().write({'order_id': order_id})
            except Exception as err:
                _logger.error(err)
                request._cr.rollback()
                info = "Gagal Create Customer Payment: %s" % (err)
                error = 'Bad Request'
                return invalid_response(400, error, info)

            name_customer_payment.append(str(create_customer_payment.name or create_customer_payment.id))
            invoices.append(invoice_id)

        name = "Success Create Customer Payment : %s" % name_customer_payment
        return valid_response(status=200, data=name)
    
