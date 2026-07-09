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
try:
    from packaging import version as parse_version
except ImportError:
    from odoo.tools import parse_version as parse_version

# 3:  imports of odoo
import odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
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

    @http.route('/api/v1/integration/asset/getAllData', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def get_all_data_assets(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        url = '/api/v1/integration/asset/getAllData'
        MANDATORY_FIELDS = ['company_code', 'branch_code']
        detail_message = check_mandatory_fields(params, MANDATORY_FIELDS)
        if detail_message:
            return invalid_response(400, 'mandatory_field', detail_message)
        company = request.env['res.company'].sudo().search([('profit_centre', '=', params['company_code'])], limit=1)
        if not company:
            detail_message = f"Company dengan Code {params['company_code']} tidak ditemukan."
            return self._log_and_return_error('API GET Asset Failed', url, 404, 'Company Not Found', detail_message, params)
        branch = request.env['res.company'].sudo().search([('code', '=', params['branch_code'])], limit=1)
        if not branch:
            detail_message = f"Branch dengan Code {params['branch_code']} tidak ditemukan."
            return self._log_and_return_error('API GET Asset Failed', url, 404, 'Branch Not Found', detail_message, params)
        limit = int(params.get('pageSize', 10))
        offset = int(params.get('page', 0))
        query_params = []
        query_where = " WHERE a.state != 'close' AND a.company_id = %s AND a.company_id = %s"
        query_params.extend([company.id, branch.id])
        start_date = params.get('start_last_modified_date')
        end_date = params.get('end_last_modified_date')
        if start_date and end_date:
            query_where += " AND a.write_date::date BETWEEN %s AND %s"
            query_params.extend([start_date, end_date])
        if params.get('asset_category'):
            asset_categ = request.env['account.asset.category'].sudo().search([('name', '=', params['asset_category'])], limit=1)
            if not asset_categ:
                detail_message = f"Category Asset dengan Nama '{params['asset_category']}' tidak ditemukan."
                return self._log_and_return_error('API GET Asset Failed', url, 404, 'Asset Category Not Found', detail_message, params)
            query_where += " AND a.category_id = %s"
            query_params.append(asset_categ.id)
        query = f"""
            SELECT 
            rc.profit_centre AS company_code, 
            rc.code AS branch_code, 
            a.division AS division_code,
            rp.code AS vendor_code,
            '' AS transaction_no_erp, 
            a.code AS asset_no, 
            a.name AS asset_name,
            pp.name AS product_name, 
            aac.name AS product_class, 
            a.real_purchase_value AS gross_value,
            a.value_residual AS asset_nbv, 
            TO_CHAR(a.purchase_date, 'YYYY-MM-DD HH24:MI:SS') AS asset_acquisition_date,
            TO_CHAR(a.date, 'YYYY-MM-DD HH24:MI:SS') AS asset_effective_date,
            a.method_number AS number_of_depreciation_in_months,
            (a.method_number - (SELECT count(id) FROM account_asset_depreciation_line WHERE asset_id=a.id AND move_check=True)) as number_of_depreciation_remaining_in_months,
            '1' AS asset_qty, 
            a.state AS asset_status,
            TO_CHAR(a.write_date + INTERVAL '7 Hours', 'YYYY-MM-DD HH24:MI:SS') AS last_modified_erp
            FROM account_asset_asset a
            LEFT JOIN res_company rc ON a.company_id = rc.id
            LEFT JOIN res_partner rp ON a.partner_id = rp.id
            LEFT JOIN account_asset_category aac ON a.category_id = aac.id
            LEFT JOIN product_product pp ON a.product_id = pp.id
            {query_where} ORDER BY a.id DESC LIMIT %s OFFSET %s """
        query_params.extend([limit, offset])
        try:
            request.env.cr.execute(query, tuple(query_params))
            results = request.env.cr.dictfetchall()
        except Exception as err:
            _logger.error(err); request.env.cr.rollback()
            return self._log_and_return_error('API GET Asset Failed', url, 500, "Failed When Execute Query!", str(err), params)
        if not results:
            return valid_response("success", "Data Asset Kosong", [], 0, offset, limit)
        return valid_response("success", "Successfully", results, len(results), offset, limit)


    @http.route('/api/v1/integration/asset/mutasi', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_data_asset_mutasi(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))        
        header = params.get('header')
        details = params.get('details')
        url = '/api/v1/integration/asset/mutasi'

        if not header or not details:
            return self._log_and_return_error('API Asset Mutation Failed', url, 400, "Request Body Error", "Header atau Details tidak ditemukan.", params)

        detail_message = check_mandatory_fields(header, ['mutasi_no_koprol', 'branch_code', 'branch_code_destination', 'tanggal_mutasi'])
        if not detail_message:
            for i, detail in enumerate(details):
                detail_message += check_mandatory_fields(detail, ['asset_no'])
        if detail_message:
            return self._log_and_return_error('API Asset Mutation Failed', url, 400, 'mandatory_field', detail_message, params)

        koprol_code = header['mutasi_no_koprol']
        if request.env['tw.asset.mutation'].sudo().search_count([('koprol_code', '=', koprol_code)]) > 0:
            return self._log_and_return_error('API Asset Mutation Failed', url, 409, "Conflict", f"Nomor Mutasi {koprol_code} sudah digunakan.", params)

        branch_dest = request.env['res.company'].sudo().search([('code', '=', header['branch_code_destination'])], limit=1)
        if not branch_dest:
            return self._log_and_return_error('API Asset Mutation Failed', url, 404, 'Destination Branch Not Found', f"Cabang Tujuan kode {header['branch_code_destination']} tidak ditemukan.", params)

        branch_sender = request.env['res.company'].sudo().search([('code', '=', header['branch_code'])], limit=1)
        if not branch_sender:
            return self._log_and_return_error('API Asset Mutation Failed', url, 404, 'Branch Not Found', f"Cabang Pengirim kode {header['branch_code']} tidak ditemukan.", params)

        asset_lines = []
        for item in details:
            asset = request.env['account.asset.asset'].sudo().search([('code', '=', item['asset_no'])], limit=1)
            if not asset:
                return self._log_and_return_error('API Asset Mutation Failed', url, 404, 'Asset Not Found', f"Aset dengan nomor {item['asset_no']} tidak terdaftar di sistem.", params)
            asset_lines.append((0, 0, {'asset_id': asset.id, 'location_asset_id': asset.location_id.id}))

        vals = {
            'koprol_code': koprol_code,
            'date': header['tanggal_mutasi'],
            'last_modified_date': header.get('last_modified_koprol'),
            'company_id': branch_sender.company_id.id, # Asumsi cabang terhubung ke company
            'company_request_id': branch_dest.company_id.id,
            'detail_ids': asset_lines,
        }

        try:
            mutation = request.env['tw.asset.mutation'].sudo().create(vals)
            # Jika perlu konfirmasi otomatis
            # mutation.action_confirm() 
            data = {'mutasi_no_koprol': mutation.koprol_code, 'mutasi_no_erp': mutation.name}
            create_api_log(name='API Asset Mutation Success', url=url, request_data=params, response_code=200, response_data=str(data))
            return valid_response("success", "Mutasi Asset Berhasil diposting.", data)
        except (UserError, ValidationError) as err:
            _logger.error(err); request.env.cr.rollback()
            return self._log_and_return_error('API Asset Mutation Failed', url, 400, "Validation Error", str(err.name), params)
        except Exception as err:
            _logger.error(err); request.env.cr.rollback()
            return self._log_and_return_error('API Asset Mutation Failed', url, 500, "Internal Server Error", str(err), params)

    @http.route('/api/v1/integration/asset/disposal', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_data_asset_disposal(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        header = params.get('header')
        details = params.get('details')
        attachments = params.get('attachments')
        url = '/api/v1/integration/asset/disposal'

        if not header or not details:
            return self._log_and_return_error('API Disposal Asset Failed', url, 400, "Request Body Error", "Header atau Details tidak ditemukan.", params)

        MANDATORY_HEADER = ['transaction_no_koprol', 'branch_code', 'transaction_date', 'transaction_type']
        detail_message = check_mandatory_fields(header, MANDATORY_HEADER)
        if header.get('transaction_type','').lower() != 'scrap' and 'payment_term' not in header:
            detail_message += "Fields ini tidak ada: ['payment_term']"
        if not detail_message:
            for i, detail in enumerate(details):
                detail_message += check_mandatory_fields(detail, ['asset_no', 'sales_value', 'asset_nbv'], f" (baris ke-{i+1})")
        if detail_message:
            return self._log_and_return_error('API Disposal Asset Failed', url, 400, 'mandatory_field', detail_message, params)

        koprol_code = header['transaction_no_koprol']
        if request.env['tw.asset.disposal'].sudo().search_count([('koprol_code', '=', koprol_code)]) > 0:
            return self._log_and_return_error('API Disposal Asset Failed', url, 409, "Conflict", f"Nomor Transaksi {koprol_code} sudah digunakan.", params)

        branch = request.env['res.company'].sudo().search([('code', '=', header['branch_code'])], limit=1)
        if not branch:
            return self._log_and_return_error('API Disposal Asset Failed', url, 404, 'Branch Not Found', f"Cabang dengan kode {header['branch_code']} tidak ditemukan.", params)

        vals = {
            'koprol_code': koprol_code,
            'last_modified_date': header.get('last_modified_koprol'),
            'division': header.get('division_code'),
            'date': header['transaction_date'],
            'type': 'scrap' if header['transaction_type'].lower() == 'scrap' else 'sold',
            'company_id': branch.company_id.id,
        }

        if header.get('customer'):
            customer = request.env['res.partner'].sudo().search(['|', ('default_code', '=', header['customer']), ('koprol_code', '=', header['customer'])], limit=1)
            if not customer:
                return self._log_and_return_error('API Disposal Asset Failed', url, 404, 'Customer Not Found', f"Customer {header['customer']} tidak terdaftar.", params)
            vals['partner_id'] = customer.id

        if vals['type'] == 'sold' and header.get('payment_term'):
            payment_term = request.env['account.payment.term'].sudo().search([('name', '=', header['payment_term'])], limit=1)
            if not payment_term:
                 return self._log_and_return_error('API Disposal Asset Failed', url, 404, 'Payment Term Not Found', f"Payment Term {header['payment_term']} tidak terdaftar.", params)
            vals['payment_term_id'] = payment_term.id

        asset_lines = []
        for item in details:
            asset = request.env['account.asset.asset'].sudo().search([('code', '=', item['asset_no']), ('company_id', '=', branch.company_id.id)], limit=1)
            if not asset:
                return self._log_and_return_error('API Disposal Asset Failed', url, 404, 'Asset Not Found', f"Aset {item['asset_no']} tidak ditemukan di cabang tersebut.", params)
            if fields.Date.from_string(header['transaction_date']) < asset.date:
                return self._log_and_return_error('API Disposal Asset Failed', url, 400, 'Invalid Date', f"Tanggal disposal {header['transaction_date']} tidak boleh sebelum tanggal perolehan aset {asset.date}.", params)
            
            tax_ids = []
            if item.get('tax_ids'):
                for tax in item['tax_ids']:
                    tax_obj = request.env['account.tax'].sudo().search([('name', '=', tax['tax_code']), ('type_tax_use', '=', 'sale')], limit=1)
                    if tax_obj: tax_ids.append(tax_obj.id)
            
            asset_lines.append((0, 0, {
                'asset_id': asset.id, 'amount': item['sales_value'],
                'tax_id': [(6, 0, tax_ids)] if tax_ids else False,
            }))
        
        if vals['type'] == 'scrap': vals['disposal_line_scrap_ids'] = asset_lines
        else: vals['disposal_line_sold_ids'] = asset_lines

        try:
            disposal = request.env['tw.asset.disposal'].sudo().create(vals)
            if attachments:
                disposal.sudo().create_attachment_file_disposal_assets(attachments)
            
            # TODO: Jika perlu approval & konfirmasi otomatis
            # disposal.action_request_approval()
            # disposal.sudo().approva_all_approval(reason='Auto Approve (Koprol)')
            # disposal.confirm_disposal()

            data = {'transaction_no_koprol': disposal.koprol_code, 'transaction_no_erp': disposal.name}
            create_api_log(name='API Disposal Asset Success', url=url, request_data=params, response_code=200, response_data=str(data))
            return valid_response("success", "Disposal Asset Berhasil.", data)
        except (UserError, ValidationError) as err:
            _logger.error(err); request.env.cr.rollback()
            return self._log_and_return_error('API Disposal Asset Failed', url, 400, "Validation Error", str(err.name), params)
        except Exception as err:
            _logger.error(err); request.env.cr.rollback()
            return self._log_and_return_error('API Disposal Asset Failed', url, 500, "Internal Server Error", str(err), params)