#!/usr/bin/python#!/usr/bin/python
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
    
def check_empty(value):
    return False if value == '' else value

class ControllerREST(http.Controller):

    def _log_and_return_error(self, name, url, code, message, detail_message, payload, header_vals={}):
        """Helper function to log an error and return an invalid response."""
        ip_address = request.httprequest.remote_addr
        
        # 1. Buat response error terlebih dahulu dan simpan dalam variabel
        error_response = invalid_response(code, message, detail_message)
        
        # 2. Panggil create_api_log dengan menyertakan variabel 'error_response'
        request.env['tw.api.log'].sudo().create_api_log(
            name=name,
            url=url,
            description=str(detail_message),
            ip_address=ip_address,
            response=str(error_response),
            payload=payload,
            header=str(header_vals),
        )
        
        # 3. Kembalikan response yang sudah dibuat
        return error_response

    @http.route('/api/v1/integration/purchaseOrder/create', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_purchase_order_create(self, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        po_header = post.get('header', {})
        po_details = post.get('details', [])
        
        MANDATORY_FIELDS = ['header', 'details']
        MANDATORY_HEADER_FIELDS = [
            'company_code', 'branch_code', 'division_code', 'department_code', 'spt_date',
            'purchase_order_no_erp', 'purchase_order_no_koprol', 'vendor_code',
            'purchase_order_status', 'currency', 'approval_status', 'po_type',
            'delivery_date', 'terms_of_payment', 'last_modified_koprol'
        ]
        MANDATORY_DETAILS_FIELDS = [
            'po_line_no_koprol', 'product_no', 'product_name', 'category_code',
            'product_class', 'order_qty', 'product_uom', 'unit_price', 'discount_amount',
            'subtotal_price', 'tax_code', 'tax_included_in_price', 'is_fixed_asset',
            'asset_number', 'company_code', 'branch_code', 'division_code',
            'department_code', 'description'
        ]

        # --- Validation ---
        detail_message = check_mandatory_fields(post, MANDATORY_FIELDS)
        if not detail_message:
            detail_message += check_mandatory_fields(po_header, MANDATORY_HEADER_FIELDS)
            for data in po_details:
                detail_message += check_mandatory_fields(data, MANDATORY_DETAILS_FIELDS)
        
        if detail_message:
            return invalid_response(400, 'mandatory_field', detail_message)

        po_number = po_header.get('purchase_order_no_koprol')
        message = f"Purchase Order No. {po_number} ditolak"

        # --- Check for Existing PO ---
        if request.env['purchase.order.asset'].sudo().search_count([('partner_ref', '=', po_number)]) > 0:
            detail_message = f"No PO {po_number} sudah ada"
            return self._log_and_return_error(
                name=f"Failed Purchase Order Asset, {detail_message}",
                url='/api/v1/integration/purchaseOrder/create',
                code=409, message=message, detail_message=detail_message, payload=post
            )

        # --- Process Order Lines ---
        order_line = []
        for item in po_details:
            product_no = item.get('product_no')
            product_obj = request.env['product.product'].sudo().search(
                ['|', ('default_code', '=', product_no), ('koprol_code', '=', product_no)], limit=1)
            
            if not product_obj:
                detail_message = f"Product dengan product_no {product_no} tidak ditemukan!"
                return self._log_and_return_error(
                    name=f"Failed PO Asset, product not found",
                    url='/api/v1/integration/purchaseOrder/create',
                    code=404, message=message, detail_message=detail_message, payload=post
                )

            tax_obj = False
            tax_code = item.get('tax_code')
            if tax_code:
                tax_included = 'tax_included' if item.get('tax_included_in_price', False) else 'tax_excluded'
                tax_obj = request.env['account.tax'].sudo().search([
                    ('type_tax_use', '=', 'purchase'), ('name', '=', tax_code),
                    ('price_include_override', '=', tax_included)], limit=1)
                if not tax_obj:
                    detail_message = f"Tax dengan tax_code {tax_code} tidak ditemukan!"
                    return self._log_and_return_error(
                        name=f"Failed PO Asset, tax not found",
                        url='/api/v1/integration/purchaseOrder/create',
                        code=404, message=message, detail_message=detail_message, payload=post
                    )
            
            if item.get('is_fixed_asset') and not product_obj.asset_category_id:
                product_class = item.get('product_class')
                asset_category = request.env['account.asset.category'].sudo().search([('name', '=', product_class)], limit=1)
                if not asset_category:
                    detail_message = f"Asset Category {product_class} belum ditambahkan di ERP!"
                    return self._log_and_return_error(
                        name=f"Failed PO Asset, asset category not found",
                        url='/api/v1/integration/purchaseOrder/create',
                        code=404, message=message, detail_message=detail_message, payload=post
                    )
                product_obj.sudo().write({'asset_category_id': asset_category.id})
            
            order_line.append((0, 0, {
                'product_id': product_obj.id,
                'koprol_id': item.get('po_line_no_koprol'),
                'name': item.get('description'),
                'price_unit': item.get('unit_price'), # Pastikan nama field di model line sesuai
                'product_qty': item.get('order_qty'), # Pastikan nama field di model line sesuai
                'is_asset': item.get('is_fixed_asset'),
                'taxes_id': [(6, 0, [tax_obj.id])] if tax_obj else False,
            }))

        # --- Find Company and Supplier ---
        company_obj = request.env['res.company'].sudo().search([('profit_centre', '=', po_header.get('company_code'))], limit=1)
        if not company_obj:
            detail_message = f"Company dengan company_code {po_header.get('company_code')} tidak ditemukan!"
            return self._log_and_return_error(
                name=f"Failed PO Asset, company not found",
                url='/api/v1/integration/purchaseOrder/create',
                code=404, message=message, detail_message=detail_message, payload=post
            )

        supplier_obj = request.env['res.partner'].sudo().search([('code', '=', po_header.get('vendor_code'))], limit=1)
        if not supplier_obj:
            detail_message = "PO memiliki nomor Vendor yang tidak valid!"
            return self._log_and_return_error(
                name=f"Failed PO Asset, supplier not found",
                url='/api/v1/integration/purchaseOrder/create',
                code=404, message=message, detail_message=detail_message, payload=post
            )
        
        # --- Create Purchase Order ---
        request.env.company = company_obj
        vals = {
            'company_id': company_obj.id,
            'partner_id': supplier_obj.id, # Di Odoo, relasi ke supplier adalah 'partner_id'
            'partner_ref': po_number, # Menyimpan no PO eksternal
            'division': 'Umum',
            'last_modified_date': po_header.get('last_modified_koprol'),
            'order_line': order_line, # Di Odoo, relasi ke line adalah 'order_line'
            # 'payment_term_id': po_header.get('terms_of_payment'), # Perlu mapping jika format berbeda
            'start_date': po_header.get('delivery_date'),
            'end_date': po_header.get('delivery_date'),
            'date_planned': po_header.get('delivery_date'),
            'po_type': po_header.get('po_type')
        }
        
        try:
            po = request.env['purchase.order.asset'].with_company(company_obj.id).sudo().create(vals)
            po.sudo().action_request_approval()            
            po.sudo().approva_all_approval(reason='Auto Approve (Koprol)')
            po.sudo().action_confirm()
            
            details_response = [{
                'po_line_no_koprol': data.koprol_id,
                'product_no': data.product_id.koprol_code or data.product_id.default_code,
                'order_qty': data.product_qty
            } for data in po.order_line]

        except Exception as err:
            request._cr.rollback()
            return self._log_and_return_error(
                name=f"Failed to create PO Asset: {str(err)}",
                url='/api/v1/integration/purchaseOrder/create',
                code=500, message=message, detail_message=str(err), payload=post, header_vals=vals
            )

        data = { 
            "purchase_order_no_koprol": po_number,
            "purchase_order_no_erp": po.name,
            "details": details_response
        }
        return valid_response("success", "Purchase Order berhasil diposting", data)

    @http.route('/api/v1/integration/purchaseOrder/cancel', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_purchase_order_cancel(self, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        
        MANDATORY_FIELDS = ['purchase_order_no_koprol', 'purchase_order_no_erp', 'close_reason']
        detail_message = check_mandatory_fields(post, MANDATORY_FIELDS)
        if detail_message:
            return invalid_response(400, 'mandatory_field', detail_message)
        
        reference = post.get('purchase_order_no_koprol')
        name = post.get('purchase_order_no_erp')
        reason = post.get('close_reason')
        message = f"PO No. {reference} gagal dibatalkan"

        po_obj = request.env['purchase.order.asset'].sudo().search([('name', '=', name), ('partner_ref', '=', reference)], limit=1)
        
        if not po_obj:
            detail_message = f"PO tidak ditemukan dengan No. ERP {name} dan No. Koprol {reference}"
            return self._log_and_return_error(
                name=f"Failed PO Cancel, not found",
                url='/api/v1/integration/purchaseOrder/cancel',
                code=404, message=message, detail_message=detail_message, payload=post
            )
        
        if po_obj.state == 'cancel':
            detail_message = "PO sudah dalam status cancel"
            return self._log_and_return_error(
                name=f"Failed PO Cancel, already cancelled",
                url='/api/v1/integration/purchaseOrder/cancel',
                code=409, message=message, detail_message=detail_message, payload=post
            )
        
        try:
            # Menggunakan logika validasi dari model purchase.order.asset
            # Asumsi: Method validasi ada di dalam action_cancel atau bisa dipanggil
            # Untuk contoh, kita asumsikan validasi GR/GRC ada di action_cancel
            po_obj.sudo().button_cancel() # Method standar Odoo untuk cancel
            po_obj.sudo().write({'cancel_reason': reason})
            
            data = {
                'purchase_order_no_koprol': reference,
                'purchase_order_no_erp': name,
                'purchase_order_status': 'CANCELED',
                'close_reason': reason
            }
            return valid_response("success", f"Purchase Order No. {reference} berhasil dibatalkan", data)

        except (UserError, ValidationError) as err:
            request._cr.rollback()
            return self._log_and_return_error(
                name=f"Failed PO Cancel, validation error: {str(err.name)}",
                url='/api/v1/integration/purchaseOrder/cancel',
                code=400, message=message, detail_message=str(err.name), payload=post
            )
        except Exception as err:
            request._cr.rollback()
            return self._log_and_return_error(
                name=f"Failed PO Cancel, generic error: {str(err)}",
                url='/api/v1/integration/purchaseOrder/cancel',
                code=500, message=message, detail_message=str(err), payload=post
            )

    @http.route('/api/v1/integration/purchaseOrder/getData', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def get_purchase_order_data(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        
        MANDATORY_FIELDS = ['company_code', 'vendor_code', 'purchase_order_no_erp', 'purchase_order_no_koprol']
        detail_message = check_mandatory_fields(params, MANDATORY_FIELDS)
        if detail_message:
            return invalid_response(400, 'mandatory_field', detail_message)

        po_koprol_number = params.get('purchase_order_no_koprol')
        po_erp_number = params.get('purchase_order_no_erp')
        company_code = str(params.get('company_code'))
        vendor_code_erp = params.get('vendor_code_erp', False) # Asumsi ada vendor_code_erp
        
        query_params = []
        query_where = " WHERE 1=1 "

        if company_code:
            query_where += " AND rc.profit_centre = %s"
            query_params.append(company_code)
        
        if vendor_code_erp:
            query_where += " AND rp.code = %s"
            query_params.append(vendor_code_erp)
        
        if po_koprol_number and po_erp_number:
            query_where += " AND (poa.name = %s OR poa.partner_ref = %s)"
            query_params.extend([po_erp_number, po_koprol_number])

        query = f"""    
            SELECT 
                json_build_object(
                    'company_code', parent_company.code,
                    'branch_code', rc.code, 
                    'purchase_order_no_erp', poa.name,
                    'purchase_order_no_koprol', poa.partner_ref,
                    'vendor_code', rp.code,
                    'purchase_order_status', poa.state,
                    'division_code', poa.division,
                    'department_code', '',
                    'po_type', poa.po_type,
                    'delivery_date', TO_CHAR(poa.date_planned, 'YYYY-MM-DD HH24:MI:SS'),
                    'last_modified_erp', TO_CHAR(poa.write_date + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS')
                ) AS header,
                (
                    SELECT json_agg(
                        json_build_object(
                            'po_line_no_erp', pol.id,
                            'po_line_no_koprol', pol.koprol_id,
                            'product_no', pp.default_code,
                            'order_qty', COALESCE(pol.product_qty, 0),
                            'receipt_qty', COALESCE(pol.qty_received, 0),
                            'remaining_qty', COALESCE(pol.product_qty, 0) - COALESCE(pol.qty_received, 0)
                        )
                    ) 
                    FROM purchase_order_asset_line pol
                    LEFT JOIN product_product pp ON pp.id = pol.product_id
                    WHERE pol.order_id = poa.id
                ) AS details
            FROM purchase_order_asset poa
            LEFT JOIN res_company rc ON poa.company_id = rc.id
            LEFT JOIN res_company parent_company ON parent_company.id = rc.parent_id
            LEFT JOIN res_partner rp ON poa.partner_id = rp.id
            {query_where}
            LIMIT 1
        """
        
        try:
            request.env.cr.execute(query, tuple(query_params))
            results = request.env.cr.dictfetchone()
        except Exception as err:
            request._cr.rollback()
            return self._log_and_return_error(
                name=f"Failed Get Data: {str(err)}",
                url='/api/v1/integration/purchaseOrder/getData',
                code=500, message=f"Gagal mengambil data PO {po_koprol_number}", detail_message=str(err), payload=params
            )

        if not results:
            detail_message = "Data Purchase Order tidak ditemukan"
            return self._log_and_return_error(
                name="Failed Get Data, PO not found",
                url='/api/v1/integration/purchaseOrder/getData',
                code=404, message=f"Gagal mengambil data PO {po_koprol_number}", detail_message=detail_message, payload=params
            )

        return valid_response("success", "Data berhasil diambil", results)