# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)

from odoo.addons.tw_koprol.controllers.main import check_mandatory_fields, create_api_log, invalid_response, valid_response
from odoo.addons.rest_api.controllers.main import check_valid_token

class ControllerREST(http.Controller):

    def _log_and_return_error(self, name, url, code, message, detail_message, payload, header_vals={}):
        """Helper function standar untuk logging dan response error."""
        ip_address = request.httprequest.remote_addr
        error_response = invalid_response(code, message, detail_message)
        log_model = request.env['tw.api.log'].sudo()
        if hasattr(log_model, 'create_api_log'):
            log_model.create_api_log(
                name=name, url=url, description=str(detail_message), ip_address=ip_address,
                response=str(error_response), payload=payload, header=str(header_vals),
            )
        else:
            _logger.error(f"Method 'create_api_log' not found on 'tw.api.log'. Log failed for: {name}")
        return error_response

    @http.route('/api/v1/integration/employee/upsertData', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_data_employee(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        url = '/api/v1/integration/employee/upsertData'

        MANDATORY_FIELDS = [
            "nip", "name", "work_email", "mobile_no", "register_number", "join_date",
            "employee_active", "branch_code", "job_position"
        ]
        detail_message = check_mandatory_fields(item=params, mandatory_field=MANDATORY_FIELDS)
        if detail_message:
            return self._log_and_return_error('Failed Master Employee API', url, 400, 'mandatory_field', detail_message, params)

        try:
            job = request.env['hr.job'].sudo().search([('name', '=', params['job_position'])], limit=1)
            if not job:
                return self._log_and_return_error('Failed Master Employee API', url, 404, 'Job Position Not Found', f"Jabatan '{params['job_position']}' tidak ditemukan.", params)

            branch = request.env['res.company'].sudo().search([('code', '=', params['branch_code'])], limit=1)
            if not branch:
                return self._log_and_return_error('Failed Master Employee API', url, 404, 'Branch Not Found', f"Cabang dengan kode '{params['branch_code']}' tidak ditemukan.", params)

            superior = request.env['hr.employee'].sudo().search([('name', 'ilike', params.get('superior_name'))], limit=1)
            
            vals = {
                'registry_number': params['nip'],
                'name': params['name'],
                'work_email': params['work_email'],
                'mobile_phone': params['mobile_no'],
                'identification_id': params['register_number'], 
                'working_start_date': params['join_date'],
                'active': params['employee_active'].lower() == 'active',
                'is_user': True, 
                'company_id': branch.id,
                'job_id': job.id,
                'department_id': job.department_id.id,
                'coach_id': superior.id if superior else False,
                'last_modified_date': params.get('last_modified_koprol'),
            }
            
            if params.get('account_number'):
                bank = request.env['res.bank'].sudo().search([('name', '=', params.get('bank_code','').upper())], limit=1)
                vals['bank_account_id'] = request.env['res.partner.bank'].sudo().find_or_create(
                    params['account_number'],
                    {
                        'bank_id': bank.id if bank else False,
                        'acc_holder_name': params.get('account_name')
                    }
                ).id

            employee = request.env['hr.employee'].sudo().create(vals)

            if params.get('old_nip'):
                old_employee = request.env['hr.employee'].sudo().search([('registry_number', '=', params['old_nip'])])
                if old_employee:
                    old_employee.sudo().write({'active': False, 'working_end_date': fields.Date.today()})

            data = {"nip": employee.registry_number, "employee_no_erp": employee.registry_number}
            self._log_and_return_error('Success Master Employee API', url, 200, 'success', str(data), params)
            return valid_response("success", "Data Employee berhasil diproses", data)

        except (UserError, ValidationError) as err:
            _logger.error(err)
            request.env.cr.rollback()
            return self._log_and_return_error('Failed Master Employee API', url, 400, "Validation Error", str(err.name), params)
        except Exception as err:
            _logger.error(err)
            request.env.cr.rollback()
            return self._log_and_return_error('Failed Master Employee API', url, 500, "Internal Server Error", str(err), params)