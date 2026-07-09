#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json
import logging

from odoo import http
from odoo.addons.rest_api.controllers.main import check_valid_token
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response
from odoo.http import request

_logger = logging.getLogger(__name__)


class TwPettyCashOutApi(http.Controller):
    def _bad_request(self, info):
        _logger.error(info)
        return invalid_response(400, 'Bad Request', info)

    def _get_employee(self, payload, branch):
        employee_obj = request.env['hr.employee'].sudo()
        if payload.get('employee_id'):
            try:
                employee = employee_obj.browse(int(payload.get('employee_id'))).exists()
            except (TypeError, ValueError):
                employee = employee_obj
            if employee:
                return employee

        employee_code = (
            payload.get('employee_code')
            or payload.get('registry_number')
            or payload.get('nik')
            or payload.get('barcode')
        )
        if employee_code:
            for field_name in ('registry_number', 'employee_code', 'nik', 'barcode', 'identification_id', 'pin'):
                if field_name in employee_obj._fields:
                    employee = employee_obj.search([(field_name, '=', employee_code)], limit=1)
                    if employee:
                        return employee

        if payload.get('employee_name'):
            employee = employee_obj.search([('name', '=', payload.get('employee_name'))], limit=1)
            if employee:
                return employee

        employee = employee_obj.search([('user_id', '=', request.env.user.id)], limit=1)
        if employee:
            return employee

        return employee_obj.search([('company_id', '=', branch.id)], limit=1)

    def _get_petty_cash_journal(self, payload, branch):
        branch_config = request.env['tw.branch.setting'].sudo().search([('company_id', '=', branch.id)], limit=1)
        journal = branch_config.account_setting_id.pettycash_journal_id
        if journal:
            return journal

        journal_obj = request.env['account.journal'].sudo()
        if payload.get('journal_id'):
            try:
                journal = journal_obj.browse(int(payload.get('journal_id'))).exists()
            except (TypeError, ValueError):
                journal = journal_obj
            if journal:
                return journal

        journal_code = payload.get('journal_code') or payload.get('petty_cash_journal_code')
        if journal_code:
            journal = journal_obj.search([
                ('code', '=', journal_code),
                ('type', '=', 'petty_cash'),
                '|',
                ('company_id', '=', False),
                ('company_id', 'parent_of', branch.id),
            ], limit=1)
            if journal:
                return journal

        return journal_obj.search([
            ('type', '=', 'petty_cash'),
            '|',
            ('company_id', '=', False),
            ('company_id', 'parent_of', branch.id),
        ], limit=1)

    @http.route('/api/tw_petty_cash_out/v1/post_create_petty_cash_out/', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_create_petty_cash_out(self, **post):
        payload = json.loads(request.httprequest.get_data(as_text=True))

        branch_code = payload.get('branch_code')
        division = payload.get('division')
        ref = payload.get('ref')

        if not branch_code:
            return self._bad_request("branch_code harus diisi")

        try:
            amount = float(payload.get('amount') or 0.0)
        except (TypeError, ValueError):
            return self._bad_request("Amount petty cash tidak valid: %s" % payload.get('amount'))
        if amount <= 0.0:
            return self._bad_request("Amount petty cash harus lebih dari 0")

        branch = request.env['res.company'].sudo().search([('code', '=', branch_code)], limit=1)
        if not branch:
            return self._bad_request("invalid data for kode branch [%s]" % branch_code)

        if not division:
            return self._bad_request("division harus diisi")

        journal = self._get_petty_cash_journal(payload, branch)
        if not journal:
            return self._bad_request("Konfigurasi jurnal petty cash cabang belum dibuat, silahkan setting dulu !")

        employee = self._get_employee(payload, branch)
        if not employee:
            return self._bad_request("Employee petty cash tidak ditemukan !")

        partner = employee.work_contact_id or employee.address_home_id or employee.user_id.partner_id
        vals = {
            'company_id': branch.id,
            'branch_destination_id': branch.id,
            'employee_id': employee.id,
            'receiver_id': partner.id if partner else False,
            'amount': amount,
            'journal_petty_id': journal.id,
            'division': division,
        }

        payment_fields = request.env['tw.petty.cash.out']._fields
        if 'ref' in payment_fields:
            vals['ref'] = ref
        elif 'memo' in payment_fields:
            vals['memo'] = ref
        if 'journal_id' in payment_fields:
            vals['journal_id'] = journal.id
        if 'payment_type' in payment_fields:
            vals['payment_type'] = 'outbound'
        if 'partner_type' in payment_fields:
            vals['partner_type'] = 'supplier'
        if 'partner_id' in payment_fields and partner:
            vals['partner_id'] = partner.id

        try:
            petty_cash = request.env['tw.petty.cash.out'].sudo().with_company(branch).create(vals)
        except Exception as err:
            request._cr.rollback()
            info = "Gagal Create Petty Cash Out : %s" % err
            _logger.error(err)
            return invalid_response(400, 'Bad Request', info)

        name = "Success Create Petty Cash Out TEDS: '%s'" % (petty_cash.name or petty_cash.id)
        return valid_response(status=200, data=name)
