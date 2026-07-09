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

    def _get_employee(self, post):
        employee_obj = request.env['hr.employee'].sudo()
        if post.get('employee_id'):
            return employee_obj.browse(int(post.get('employee_id'))).exists()

        employee_code = post.get('employee_code') or post.get('registry_number') or post.get('nik') or post.get('barcode')
        if employee_code:
            code_domains = []
            for field_name in ('registry_number', 'employee_code', 'nik', 'barcode', 'identification_id', 'pin'):
                if field_name in employee_obj._fields:
                    code_domains.append((field_name, '=', employee_code))
            for domain in code_domains:
                employee = employee_obj.search([domain], limit=1)
                if employee:
                    return employee

        if post.get('employee_name'):
            return employee_obj.search([('name', '=', post.get('employee_name'))], limit=1)

        return employee_obj

    @http.route('/api/tw_advance_payment/v1/post_create_advance_payment/', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_create_advance_payment(self, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        branch_code = post.get('branch_code')
        memo = post.get('memo')
        date_due = post.get('date_due') or post.get('due_date') or post.get('date')

        try:
            amount = float(post.get('amount') or post.get('planning_amount_total') or 0.0)
        except (TypeError, ValueError):
            info = "Invalid amount advance payment: %s" % (post.get('amount') or post.get('planning_amount_total'))
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        branch = request.env['res.company'].sudo().search([('code', '=', branch_code)], limit=1)
        if not branch:
            info = "invalid data for kode branch [%s]" % (branch_code)
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        if not date_due:
            info = "Due Date advance payment harus diisi !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        employee = self._get_employee(post)
        if not employee:
            info = "Employee tidak ditemukan !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        if amount <= 0.0:
            info = "Amount advance payment harus lebih dari 0!"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        if employee.department_id.complete_name == 'Sparepart':
            division = 'Sparepart'
        else:
            division = post.get('division') or 'Unit'

        branch_setting_obj = request.env['tw.branch.setting'].sudo().search([('company_id', '=', branch.id)], limit=1)
        if not branch_setting_obj:
            info = "Konfigurasi cabang belum dibuat, silahkan setting dulu !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        account_setting_id = branch_setting_obj.account_setting_id
        if not account_setting_id:
            info = "Konfigurasi account cabang belum dibuat, silahkan setting dulu !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        journal = account_setting_id.journal_avp_id
        if not journal:
            info = "Journal Advance Payment is not set for branch %s." % branch.name
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        account_avp = journal.default_debit_account_id
        if not account_avp:
            info = "Default Debit Account Journal Advance Payment cabang belum dibuat, silahkan setting dulu !"
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        partner = employee.work_contact_id or (employee.user_id and employee.user_id.partner_id)
        if not partner:
            info = "Employee [%s] tidak memiliki partner yang valid !" % employee.name
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        employee_bank = employee.sudo().bank_account_id
        if not employee_bank:
            info = "Informasi Bank pada Employee %s Kosong ! Mohon Hubungi HR untuk Melengkapi Data Di HR Employee." % employee.name
            error = 'Bad Request'
            _logger.error(info)
            return invalid_response(400, error, info)

        bank_name = employee_bank.bank_id.name if employee_bank.bank_id else ''
        no_rek_tujuan = "[%s %s] %s %s" % (
            employee_bank.acc_number or '',
            bank_name,
            employee.name or '',
            branch.name or '',
        )

        vals = {
            'company_id': branch.id,
            'employee_id': employee.id,
            'partner_id': partner.id,
            'partner_bank_id': employee_bank.id,
            'division': division,
            'type': 'advance_payment',
            'payment_type': 'outbound',
            'amount': amount,
            'due_date': date_due,
            'journal_id': journal.id,
            'account_avp_id': account_avp.id,
            'email': getattr(employee, 'work_email', False) or False,
            'account_number': no_rek_tujuan,
            'description': 'Advance Payment Perjalanan Dinas - ' + str(memo or ''),
        }

        try:
            advance_payment = request.env['tw.advance.payment'].sudo().with_company(branch).create(vals)
        except Exception as err:
            request._cr.rollback()
            info = "Gagal Create Advance Payment : %s" % (err)
            error = 'Bad Request'
            _logger.error(err)
            return invalid_response(400, error, info)

        name = "Success Create Advance Payment TEDS: '%s'" % (advance_payment.name or advance_payment.id)
        return valid_response(status=200, data=name)
    
