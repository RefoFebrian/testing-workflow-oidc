# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_datetime

try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)

# Asumsi fungsi-fungsi ini ada dan diimpor dengan benar dari addon Anda
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

    @http.route('/api/v1/integration/apVoucher/getGR', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def get_data_ap_voucher_gr(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        url = '/api/v1/integration/apVoucher/getGR'

        detail_message = check_mandatory_fields(params, ['company_code', 'branch_code', 'vendor_code', 'purchase_order_no_erp'])
        if detail_message:
            return invalid_response(400, 'mandatory_field', detail_message)

        company = request.env['res.company'].sudo().search([('profit_centre', '=', params['company_code'])], limit=1)
        if not company:
            return self._log_and_return_error('Failed API Detail GR', url, 404, 'Company Not Found', f"Company dengan kode {params['company_code']} tidak ditemukan.", params)

        vendor = request.env['res.partner'].sudo().search([('code', '=', params['vendor_code'])], limit=1)
        if not vendor:
            return self._log_and_return_error('Failed API Detail GR', url, 404, 'Vendor Not Found', f"Vendor dengan kode {params['vendor_code']} tidak ditemukan.", params)

        po = request.env['purchase.order.asset'].sudo().search([('name', '=', params['purchase_order_no_erp']), ('partner_id', '=', vendor.id)], limit=1)
        if not po:
            return self._log_and_return_error('Failed API Detail GR', url, 404, 'PO Not Found', f"PO {params['purchase_order_no_erp']} untuk vendor tersebut tidak ditemukan.", params)

        domain = [('purchase_order_id', '=', po.id), ('partner_id', '=', vendor.id), ('state', '=', 'done')]
        good_receives = request.env['stock.picking'].sudo().search(domain)

        if not good_receives:
            return self._log_and_return_error('Failed API Detail GR', url, 404, 'GR Not Found', f"Tidak ada GR yang siap diproses untuk PO {params['purchase_order_no_erp']}.", params)

        results = []
        for gr in good_receives:
            details = []
            for line in gr.move_asset_ids:
                taxes = [{'tax_code': tax.name, 'price_tax_include': tax.price_include} for tax in line.tax_ids]
                details.append({
                    'po_line_no_erp': line.purchase_order_line_id.id,
                    'product_no': line.product_id.default_code or '',
                    'receipt_qty': line.qty,
                    'product_uom': line.product_id.uom_id.name,
                    'site': gr.company_id.code or '',
                    'account_no': line.asset_category_id.account_asset_id.code or '',
                    'unit_price': line.price,
                    'discount_amount': line.discount,
                    'description': line.description,
                    'tax_ids': taxes,
                    'references_1': '', 'references_2': '', 'references_3': '', 'references_4': '', 'references_5': ''
                })
            results.append({
                'header': {
                    'purchase_order_no_erp': gr.purchase_order_id.name,
                    'nomor_surat_jalan_vendor': gr.vendor_picking_number or '',
                    'good_receipt_no_erp': gr.name,
                    'good_receipt_status': gr.state,
                    'transaction_type': gr.transaction_type or '',
                    'transaction_date': format_datetime(request.env, gr.date_done, dt_format='yyyy-MM-dd HH:mm:ss'),
                    'amount': gr.amount_total,
                },
                'details': details
            })
        return valid_response("success", "Successfully", data=results)

    @http.route('/api/v1/integration/apVoucher/create', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def create_data_ap_voucher(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        header = params.get('header')
        details = params.get('details')
        url = '/api/v1/integration/apVoucher/create'

        if not header or not details:
            return self._log_and_return_error('API Create AP Voucher Failed', url, 400, "Request Body Error", "...", params)

        MANDATORY_HEADER = ["company_code", "branch_code", "vendor_code", "transaction_date", "invoice_date", "invoice_due_date"]
        detail_message = check_mandatory_fields(header, MANDATORY_HEADER)
        if detail_message:
            return self._log_and_return_error('API Create AP Voucher Failed', url, 400, 'mandatory_field', detail_message, params)

        company = request.env['res.company'].sudo().search([('profit_centre', '=', header['company_code'])], limit=1)
        if not company:
            return self._log_and_return_error('API Create AP Voucher Failed', url, 404, 'Company Not Found', "...", params)
        branch = request.env['res.company'].sudo().search([('code', '=', header['branch_code'])], limit=1)
        if not branch:
             return self._log_and_return_error('API Create AP Voucher Failed', url, 404, 'Branch Not Found', "...", params)
        vendor = request.env['res.partner'].sudo().search([('code', '=', header['vendor_code'])], limit=1)
        if not vendor:
             return self._log_and_return_error('API Create AP Voucher Failed', url, 404, 'Vendor Not Found', "...", params)

        try:
            gr_names = list(set([d['good_receipt_no_erp'] for d in details]))
            gr_records = request.env['stock.picking'].sudo().search([('name', 'in', gr_names), ('state', '=', 'done')])
            gr_map = {gr.name: gr for gr in gr_records}
            gr_ids = [gr.id for gr in gr_records]

            if len(gr_names) != len(gr_records):
                found_grs = set(gr_map.keys())
                missing_grs = set(gr_names) - found_grs
                return self._log_and_return_error('API Create AP Voucher Failed', url, 404, "GR Not Found/Ready", f"GR berikut tidak ditemukan atau statusnya bukan 'Done': {list(missing_grs)}", params)

            line_ids = []
            for detail in details:
                gr = gr_map.get(detail['good_receipt_no_erp'])
                gr_line = gr.move_asset_ids.filtered(lambda l: l.purchase_order_line_id.id == detail['po_line_no_erp'])
                if not gr_line:
                    return self._log_and_return_error('API Create AP Voucher Failed', url, 404, "GR Line Not Found", "...", params)
                
                tax_ids_from_payload = [t['tax_code'] for t in detail.get('tax_ids', [])]
                tax_ids = request.env['account.tax'].sudo().search([('name', 'in', tax_ids_from_payload), ('type_tax_use', '=', 'purchase')]).ids

                line_ids.append((0, 0, {
                    'collecting_good_receive_id': gr_line[0].id,
                    'purchase_order_id': gr_line[0].purchase_order_id.id,
                    'purchase_order_line_id': gr_line[0].purchase_order_line_id.id,
                    'product_id': gr_line[0].product_id.id,
                    'description': detail['description'],
                    'qty': gr_line[0].qty,
                    'price': detail['bill_unit_price'],
                    'discount': detail['discount_unit_price'],
                    'tax_ids': [(6, 0, tax_ids)],
                    'references_1': detail.get('references_1'), 'references_2': detail.get('references_2'),
                    'references_3': detail.get('references_3'), 'references_4': detail.get('references_4'),
                    'references_5': detail.get('references_5'),
                }))
            
            vals = {
                'company_id': branch.id,
                'partner_id': vendor.id,
                'date': header['transaction_date'],
                'document_no': header.get('vendor_invoice_number'),
                'document_date': header['invoice_date'],
                'no_faktur_pajak': header.get('tax_number'),
                'description': header.get('invoice_description'),
                'good_receive_ids': [(6, 0, gr_ids)],
                'line_ids': line_ids,
            }
            ap_voucher = request.env['tw.good.receive.collecting'].sudo().create(vals)
            ap_voucher.sudo().action_confirm()

            data = {'ap_voucher_no_erp': ap_voucher.name}
            return valid_response("success", "Data AP Voucher Berhasil Disimpan.", data)
        except (UserError, ValidationError) as err:
            return self._log_and_return_error('API Create AP Voucher Failed', url, 400, "Validation Error", str(err.name), params)
        except Exception as err:
            return self._log_and_return_error('API Create AP Voucher Failed', url, 500, "Internal Server Error", str(err), params)

    @http.route('/api/v1/integration/apVoucher/getAll', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def get_all_data_ap_voucher(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        url = '/api/v1/integration/apVoucher/getAll'

        detail_message = check_mandatory_fields(params, ['company_code', 'branch_code'])
        if detail_message: return invalid_response(400, 'mandatory_field', detail_message)

        page_size = int(params.get('page_size', 10))
        page = int(params.get('page', 1))
        offset = (page - 1) * page_size
        
        domain = [('company_id.profit_centre', '=', params['company_code']), ('company_id.code', '=', params['branch_code'])]

        if params.get('vendor_code'):
            domain.append(('partner_id.code', '=', params['vendor_code']))
        if params.get('ap_voucher_no_erp'):
            domain.append(('name', '=', params['ap_voucher_no_erp']))
        if params.get('start_invoice_date') and params.get('end_invoice_date'):
            domain.append(('invoice_id.invoice_date', '>=', params['start_invoice_date']))
            domain.append(('invoice_id.invoice_date', '<=', params['end_invoice_date']))
        if params.get('start_invoice_due_date') and params.get('end_invoice_due_date'):
            domain.append(('invoice_id.invoice_date_due', '>=', params['start_invoice_due_date']))
            domain.append(('invoice_id.invoice_date_due', '<=', params['end_invoice_due_date']))

        vouchers = request.env['tw.good.receive.collecting'].sudo().search(domain, limit=page_size, offset=offset)
        total_data = request.env['tw.good.receive.collecting'].sudo().search_count(domain)

        results = []
        for v in vouchers:
            results.append({
                'ap_voucher_no_erp': v.name,
                'company_code': v.company_id.profit_centre,
                'branch_code': v.company_id.code,
                'vendor_code_erp': v.partner_id.code,
                'transaction_date': format_datetime(request.env, v.date, dt_format='yyyy-MM-dd HH:mm:ss'),
                'transaction_type': '', # Pastikan field ini ada di model Anda jika diperlukan
                'invoice_date': format_datetime(request.env, v.invoice_id.invoice_date, dt_format='yyyy-MM-dd HH:mm:ss') if v.invoice_id else None,
                'invoice_due_date': format_datetime(request.env, v.invoice_id.invoice_date_due, dt_format='yyyy-MM-dd HH:mm:ss') if v.invoice_id else None,
                'invoice_description': v.invoice_id.narration or '',
                'tax_number': v.no_faktur_pajak or '',
                'attachment': [], # Logika attachment perlu implementasi terpisah
                'last_modified_erp': format_datetime(request.env, v.write_date, dt_format='yyyy-MM-dd HH:mm:ss'),
            })

        return valid_response("success", "Successfully", data=results, total_data=total_data, total_page=page_size, page=page)
        
    @http.route('/api/v1/integration/apVoucher/getData', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def get_detail_data_ap_voucher(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        url = '/api/v1/integration/apVoucher/getData'
        
        ap_voucher_no_erp = params.get('ap_voucher_no_erp')
        if not ap_voucher_no_erp:
            return invalid_response(400, 'mandatory_field', 'Field ap_voucher_no_erp tidak ada')

        voucher = request.env['tw.good.receive.collecting'].sudo().search([('name', '=', ap_voucher_no_erp)], limit=1)
        if not voucher:
            return self._log_and_return_error('Failed API Detail GRC', url, 404, 'AP Voucher Not Found', f"AP Voucher {ap_voucher_no_erp} tidak ditemukan.", params)

        header = {
            'ap_voucher_no_erp': voucher.name,
            'company_code': voucher.company_id.profit_centre,
            'branch_code': voucher.company_id.code,
            'vendor_code': voucher.partner_id.code,
            'transaction_date': voucher.date,
            'transaction_type': '',
            'invoice_date': voucher.invoice_id.invoice_date,
            'invoice_due_date': voucher.invoice_id.invoice_date_due,
            'invoice_description': voucher.invoice_id.narration or '',
            'tax_number': voucher.no_faktur_pajak or '',
            'attachment': [],
            'last_modified_erp': format_datetime(request.env, voucher.write_date, dt_format='yyyy-MM-dd HH:mm:ss'),
        }
        
        details = []
        for line in voucher.line_ids:
            taxes = [{'tax_code': tax.name, 'price_tax_include': tax.price_include} for tax in line.tax_ids]
            details.append({
                'purchase_order_no_erp': line.purchase_order_id.name,
                'po_line_no_erp': line.purchase_order_line_id.id,
                'good_receipt_no_erp': line.collecting_good_receive_id.picking_id.name,
                'product_no': line.product_id.default_code,
                'bill_unit_price': line.price,
                'discount_unit_price': line.discount,
                'bill_amount': line.price_subtotal,
                'description': line.description,
                'tax_ids': taxes,
                'references_1': line.references_1 or '', 
                'references_2': line.references_2 or '',
                'references_3': line.references_3 or '', 
                'references_4': line.references_4 or '',
                'references_5': line.references_5 or '',
            })

        results = {'header': header, 'details': details}
        return valid_response("success", "Successfully", data=results)