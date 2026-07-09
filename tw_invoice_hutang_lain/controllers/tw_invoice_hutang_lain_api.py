#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.rest_api.controllers.main import check_valid_token, invalid_response, valid_response


_logger = logging.getLogger(__name__)


class TwInvoiceHutangLainAPI(http.Controller):
    def _get_branch(self, branch_code):
        if not branch_code:
            return request.env['res.company']
        return request.env['res.company'].sudo().search([
            ('code', '=', branch_code),
            ('parent_id', '!=', False),
        ], limit=1)

    def _get_branch_setting(self, branch):
        if 'branch_setting_id' in branch._fields and branch.branch_setting_id:
            return branch.branch_setting_id
        return request.env['tw.branch.setting'].sudo().search([('company_id', '=', branch.id)], limit=1)

    def _get_invoice_hl_journal(self, branch):
        branch_setting = self._get_branch_setting(branch)
        account_setting = branch_setting.account_setting_id if branch_setting else False
        if account_setting:
            for field_name in (
                'hl_payment_method_journal_id',
                'invoice_hutang_lain_journal_id',
                'journal_invoice_hutang_lain_id',
                'journal_hutang_lain_id',
                'wo_customer_payment_journal_id',
            ):
                if field_name in account_setting._fields and account_setting[field_name]:
                    return account_setting[field_name]

        return request.env['account.journal'].sudo().search([
            ('company_id', 'parent_of', branch.id),
            ('type', 'in', ('bank', 'cash')),
        ], limit=1)

    def _get_journal_account(self, journal):
        return journal.default_credit_account_id or journal.default_debit_account_id or journal.default_account_id

    def _get_invoice_hl_account(self, branch):
        branch_setting = self._get_branch_setting(branch)
        account_setting = branch_setting.account_setting_id if branch_setting else False
        if account_setting and 'hutang_lain_account_line_id' in account_setting._fields:
            return account_setting.hutang_lain_account_line_id
        return request.env['account.account']

    def _get_partner(self, customer_id):
        if not customer_id:
            return request.env['res.partner']
        try:
            customer_id = int(customer_id)
        except (TypeError, ValueError):
            return request.env['res.partner']
        return request.env['res.partner'].sudo().browse(customer_id).exists()

    @http.route('/api/tw_invoice_hutang_lain/v1/post_create_invoice_hutang_lain/', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_create_invoice_hutang_lain(self, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        branch_code = post.get('branch_code')
        no_hp = post.get('no_hp')
        memo = post.get('memo')
        customer_id = post.get('customer_id')
        amount = post.get('amount')

        branch = self._get_branch(branch_code)
        if not branch:
            info = "invalid data for kode branch [%s]" % (branch_code)
            _logger.error(info)
            return invalid_response(400, 'Bad Request', info)

        partner = self._get_partner(customer_id)
        if not partner:
            info = "Customer invalid data for id [%s], data not found" % (customer_id)
            _logger.error(info)
            return invalid_response(400, 'Bad Request', info)

        try:
            amount = float(amount or 0)
        except (TypeError, ValueError):
            amount = 0
        if amount <= 0:
            info = "Amount harus lebih dari 0"
            _logger.error(info)
            return invalid_response(400, 'Bad Request', info)

        journal = self._get_invoice_hl_journal(branch)
        if not journal:
            info = "Journal Hutang Lain untuk branch [%s] belum disetting!" % (branch.name)
            _logger.error(info)
            return invalid_response(400, 'Bad Request', info)

        if not self._get_journal_account(journal):
            info = "Konfigurasi jurnal account belum dibuat, silahkan setting dulu!"
            _logger.error(info)
            return invalid_response(400, 'Bad Request', info)

        account = self._get_invoice_hl_account(branch)
        if not account:
            info = "Account Line Hutang Lain belum disetting pada Account Setting!"
            _logger.error(info)
            return invalid_response(400, 'Bad Request', info)

        currency = journal.currency_id or journal.company_id.currency_id or branch.currency_id
        description = 'Telah di bayar lewat Mesin'
        if memo:
            description += ' -> %s' % memo

        vals = {
            'branch_id': branch.id,
            'partner_type': 'customer',
            'partner_id': partner.id,
            'no_hp': no_hp,
            'amount': amount,
            'journal_id': journal.id,
            'company_id': journal.company_id.id or branch.id,
            'currency_id': currency.id,
            'account_id': account.id,
            'division': 'Unit',
            'description': description,
        }

        try:
            create_invoice_hl = request.env['tw.invoice.hutang.lain'].sudo().with_company(branch).create(vals)
            create_invoice_hl.sudo().action_rfp()
        except Exception as err:
            request._cr.rollback()
            info = "Gagal Create Invoice Hutang Lain : %s" % (err)
            _logger.error(err)
            return invalid_response(400, 'Bad Request', info)

        name = "Success Create Invoice Hutang Lain: '%s'" % create_invoice_hl.name
        return valid_response(status=200, data=name)

    @http.route('/api/tw_invoice_hutang_lain/v1/get_invoice_hutang_lain/', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_invoice_hutang_lain(self, **params):
        get_name = params.get('name')
        get_no_hp = params.get('no_hp')
        if not get_name and not get_no_hp:
            return invalid_response(400, 'Bad Request', "Parameter 'name' atau 'no_hp' tidak boleh kosong!")

        domain = [('state', '=', 'waiting_for_payment')]
        if get_name:
            domain.append(('name', '=', get_name))
        if get_no_hp:
            domain.append(('no_hp', '=', get_no_hp))

        invoice_hl = request.env['tw.invoice.hutang.lain'].sudo().search(domain)
        response = []
        for record in invoice_hl:
            response.append({
                'invoice_hl_id': record.id,
                'name_hl': record.name,
                'partner_type': record.partner_type,
                'customer': record.partner_id.display_name,
                'no_hp': record.no_hp,
                'paid_amount': record.amount,
            })

        data = {
            'status': 200,
            'message': 'success',
            'response': response,
        }
        return valid_response(status=200, data=data)

    @http.route('/api/tw_invoice_hutang_lain/v1/post_paid_invoice_hutang_lain/', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_paid_invoice_hutang_lain(self, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        invoice_hl_id = post.get('id')

        invoice_hl = request.env['tw.invoice.hutang.lain'].sudo().search([
            ('id', '=', invoice_hl_id),
        ], limit=1)
        if not invoice_hl:
            info = "Invoice Hutang Lain invalid data for id [%s] , data not found" % (invoice_hl_id)
            _logger.error(info)
            return invalid_response(400, 'Bad Request', info)

        if invoice_hl.state != 'waiting_for_payment':
            info = "Invoice Hutang Lain dengan id [%s] bukan status Waiting For Payment" % (invoice_hl_id)
            _logger.error(info)
            return invalid_response(400, 'Bad Request', info)

        try:
            invoice_hl.sudo().action_paid()
        except Exception as err:
            request._cr.rollback()
            info = "Gagal Create Hutang Lain: %s" % (err)
            _logger.error(err)
            return invalid_response(400, 'Bad Request', info)

        payment_name = invoice_hl.hutang_lain_id.name or invoice_hl.hutang_lain_id.id
        name = "Success Create Hutang Lain : %s" % payment_name
        return valid_response(status=200, data=name)
