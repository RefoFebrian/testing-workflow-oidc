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

    def _has_employee_payload(self, post):
        return any(post.get(field_name) for field_name in (
            'employee_id',
            'employee_code',
            'registry_number',
            'nik',
            'barcode',
            'identification_id',
            'pin',
            'employee_name',
        ))

    def _get_employee(self, post):
        employee_obj = request.env['hr.employee'].sudo()
        if post.get('employee_id'):
            return employee_obj.browse(int(post.get('employee_id'))).exists()

        employee_codes = [
            post.get('registry_number'),
            post.get('employee_code'),
            post.get('nik'),
            post.get('barcode'),
            post.get('identification_id'),
            post.get('pin'),
        ]
        for employee_code in [code for code in employee_codes if code]:
            for field_name in ('registry_number', 'employee_code', 'nik', 'barcode', 'identification_id', 'pin'):
                if field_name in employee_obj._fields:
                    employee = employee_obj.search([(field_name, '=', employee_code)], limit=1)
                    if employee:
                        return employee

        if post.get('employee_name'):
            return employee_obj.search([('name', '=', post.get('employee_name'))], limit=1)

        return employee_obj.browse()

    @http.route('/api/tw_payment_request/v1/post_create_payment_request/', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_create_payment_request(self, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        branch_code = post.get('branch_code')
        memo = post.get('memo')
        division = post.get('division')
        transaksi_dms = post.get('transaksi_dms')
        date_due = post.get('date_due')
        payment_customer_line = post.get('payment_customer_line') or []

        branch = request.env['res.company'].sudo().search([('code', '=', branch_code)], limit=1)
        if not branch:
            info = "invalid data for kode branch [%s]" % (branch_code)
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        branch_setting = request.env['tw.branch.setting'].sudo().search([('company_id', '=', branch.id)], limit=1)
        if not branch_setting:
            info = "Konfigurasi cabang belum dibuat, silahkan setting dulu !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        account_setting = branch_setting.account_setting_id
        if not account_setting:
            info = "Konfigurasi account cabang belum dibuat, silahkan setting dulu !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        journal_obj = account_setting.journal_payment_request_id
        if not journal_obj:
            info = "Konfigurasi jurnal cabang belum dibuat, silahkan setting dulu !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)
        
        employee = self._get_employee(post)
        if self._has_employee_payload(post) and not employee:
            info = "Employee tidak ditemukan !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        if employee:
            partner = employee.work_contact_id or (employee.user_id and employee.user_id.partner_id)
            if not partner:
                info = "Employee [%s] tidak memiliki partner yang valid !" % employee.name
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
        else:
            partner = request.env['res.partner'].sudo().search([
                ('code', '=', 'UMUM-MD'),
                ('name', '=', 'UMUM')
            ], limit=1)
        if not partner:
            info = "Partner UMUM-MD / UMUM tidak ditemukan !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        payment_customer_lines = []
        total_amount = 0.0
        account_uang_saku = account_setting.account_payment_request_saku_id
        account_akomodasi = account_setting.account_payment_request_akomondasi_id

        if not account_uang_saku:
            info = "Konfigurasi account payment request uang saku belum dibuat, silahkan setting dulu !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)
        if not account_akomodasi:
            info = "Konfigurasi account payment request uang akomodasi belum dibuat, silahkan setting dulu !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        for data in payment_customer_line:
            try:
                amount = float(data.get('amount') or 0.0)
            except (TypeError, ValueError):
                info = "Invalid amount payment customer line: %s" % (data.get('amount'))
                error = 'Bad Request'
                _logger.error(info)
                return invalid_response(400, error, info)
            line_type = data.get('type')

            if line_type == 'Saku':
                desc = 'Saku Perjalanan Dinas - ' + str(memo or '')
                account_line = account_uang_saku
            else:
                desc = 'Akomodasi Perjalanan Dinas - ' + str(memo or '')
                account_line = account_akomodasi

            vals = {
                'beneficiary_company_id': branch.id,
                'account_id': account_line.id,
                'name': desc,
                'amount': amount,
                'partner_id': partner.id,
                'employee_id': employee.id if employee else False,
            }
            payment_customer_lines.append((0, 0, vals))
            total_amount += amount

        date_payment_request = fields.Date.to_date(date_due) if date_due else fields.Date.context_today(request.env['tw.payment.request'])
        liquidity_amount_currency = -total_amount
        liquidity_balance = branch.currency_id._convert(
            liquidity_amount_currency,
            branch.currency_id,
            branch,
            date_payment_request,
        )
        account = journal_obj.default_debit_account_id if liquidity_balance > 0.0 else journal_obj.default_credit_account_id
        account_id = account.id if account else journal_obj.default_account_id.id
        if not account_id:
            info = "Konfigurasi jurnal account cabang belum dibuat, silahkan setting dulu !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        vals = {
            'company_id': branch.id,
            'transaction_type': 'non_recurring',
            'partner_type': 'supplier',
            'partner_id': partner.id,
            'memo': 'Payment Request Perjalanan Dinas - ' + str(memo or ''),
            'division': division,
            'due_date': date_due,
            'document_number': transaksi_dms,
            'type': 'payment_request',
            'payment_type': 'outbound',
            'journal_id': journal_obj.id,
            'account_id': account_id,
            'amount': total_amount,
            'line_dr_ids': payment_customer_lines,
        }

        try:
            create_payment_request = request.env['tw.payment.request'].sudo().with_company(branch).create(vals)
        except Exception as err:
            request._cr.rollback()
            info = "Gagal Create Payment Request : %s" % (err)
            error = 'Bad Request'
            _logger.error(err)
            return invalid_response(400, error, info)

        name = "Success Create Payment Request TEDS: '%s'" % (create_payment_request.name or create_payment_request.id)
        return valid_response(status=200, data=name)
    
