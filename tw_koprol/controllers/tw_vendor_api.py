# -*- coding: utf-8 -*-
# Menggunakan sintaks Odoo modern
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
import re

try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)

# Asumsi fungsi-fungsi ini ada dan diimpor dengan benar
from odoo.addons.tw_koprol.controllers.main import check_mandatory_fields, create_api_log, invalid_response, valid_response
from odoo.addons.rest_api.controllers.main import check_valid_token

def clean_data(value):
    # Memastikan input adalah string sebelum membersihkan
    return re.sub(r'\D', '', str(value))

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

    @http.route('/api/v1/integration/vendor/upsertData', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_data_vendor(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        url = '/api/v1/integration/vendor/upsertData'
        vals = {}

        # --- Validasi Mandatory Fields ---
        MANDATORY_FIELDS = [
            'company_type', 'company_code', 'vendor_no_koprol', 'vendor_name', 'vendor_type', 'address',
            'identity_number', 'npwp', 'is_pkp', 'terms_of_payment', 'last_modified_koprol', 'vendor_categories'
        ]
        detail_message = check_mandatory_fields(item=params, mandatory_field=MANDATORY_FIELDS)
        for categ in params.get('vendor_categories', []):
            detail_message += check_mandatory_fields(item=categ, mandatory_field=['category_code', 'category_name'])
        if params.get('bank_account'):
            for bank in params.get('bank_account', []):
                detail_message += check_mandatory_fields(item=bank, mandatory_field=['bank_alias', 'account_number', 'account_holder'])
        if detail_message:
            return self._log_and_return_error('Failed Master Vendor API', url, 400, 'mandatory_field', detail_message, params)

        # --- Validasi Data Master ---
        company = request.env['res.company'].sudo().search([('profit_centre', '=', params['company_code'])], limit=1)
        if not company:
            return self._log_and_return_error('Failed Master Vendor API', url, 404, 'Company Not Found', f"Company dengan kode {params['company_code']} tidak ditemukan.", params)

        payment_term = request.env['account.payment.term'].sudo().search([('name', '=', params['terms_of_payment']), ('active', '=', True)], limit=1)
        if not payment_term:
            return self._log_and_return_error('Failed Master Vendor API', url, 404, 'Term Of Payment Not Found', f"Term Of Payment '{params['terms_of_payment']}' tidak ditemukan.", params)

        # --- Membangun `vals` Dictionary ---
        try:
            Partner = request.env['res.partner'].sudo()
            
            # Panggil method model untuk menangani kategori (desain yang sudah baik)
            Partner.assign_vendor_categories(params, vals)
            
            vals.update({
                'company_id': company.id,
                'is_company': True if params['company_type'] == 'company' else False,
                'koprol_code': params['vendor_no_koprol'],
                'code': params.get('vendor_no_erp'), # Menggunakan 'code' untuk vendor_no_erp
                'name': params['vendor_name'],
                'category_id': [(6, 0, vals.get('category_id', []))], # Memastikan format many2many benar
                'street': params['address'],
                'identification_number': clean_data(params['identity_number']),
                'no_npwp': clean_data(params['npwp']),
                'is_pkp': True if str(params['is_pkp']).lower() == 'true' else False,
                'alamat_npwp': params.get('address_pkp'),
                'property_supplier_payment_term_id': payment_term.id,
                'last_modified_date': params['last_modified_koprol'],
                # Mapping untuk field dari NOTE
                'property_purchase_currency_id': request.env['res.currency'].sudo().search([('name', '=', params.get('currency'))], limit=1).id,
                'email': params.get('email'),
                'phone': params.get('phone'),
                'mobile': params.get('mobile'),
                'website': params.get('website_link'),
            })

            # Panggil method model untuk memproses data (desain yang sudah baik)
            vendor_obj = Partner.process_vendor_data([vals], 'api')
            
            if params.get('bank_account') and vendor_obj:
                bank_accounts_result = vendor_obj.create_bank_accounts(params['bank_account'], vendor_obj)
                if bank_accounts_result and bank_accounts_result.get('error'):
                    request.env.cr.rollback()
                    return self._log_and_return_error('Failed Master Vendor API', url, 400, "Bank Account Error", bank_accounts_result['message'], params)

            data = {"vendor_no_koprol": vendor_obj.koprol_code, "vendor_no_erp": vendor_obj.code}
            self._log_and_return_error('Success Master Vendor API', url, 200, 'success', str(data), params)
            return valid_response("success", "Data Vendor Berhasil Disimpan", data)

        except (UserError, ValidationError) as err:
            _logger.error(err)
            request.env.cr.rollback()
            return self._log_and_return_error('Failed Master Vendor API', url, 400, "Validation Error", str(err.name), params)
        except Exception as err:
            _logger.error(err)
            request.env.cr.rollback()
            return self._log_and_return_error('Failed Master Vendor API', url, 500, "Internal Server Error", str(err), params)