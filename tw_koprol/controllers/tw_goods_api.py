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

    @http.route('/api/v1/integration/goods/upsertData', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_data_goods(self, **params):
        params = json.loads(request.httprequest.get_data(as_text=True))
        url = '/api/v1/integration/goods/upsertData'

        MANDATORY_FIELDS = [
            "product_no_koprol", "product_name", "product_type", "company_code",
            "inventory_uom", "purchase_uom", "active_status", "last_modified_koprol",
        ]
        detail_message = check_mandatory_fields(item=params, mandatory_field=MANDATORY_FIELDS)
        if detail_message:
            return self._log_and_return_error('Failed Master Goods API', url, 400, 'mandatory_field', detail_message, params)

        if params['product_type'] not in ['product', 'service', 'consu']:
            detail_message = f"Product Type '{params['product_type']}' tidak valid. Gunakan: 'product', 'service', atau 'consu'."
            return self._log_and_return_error('Failed Master Goods API', url, 400, 'Product Type Not Found', detail_message, params)

        company = request.env['res.company'].sudo().search([('profit_centre', '=', params['company_code'])], limit=1)
        if not company:
            return self._log_and_return_error('Failed Master Goods API', url, 404, 'Company Not Found', f"Company dengan kode {params['company_code']} tidak ditemukan.", params)

        product_template = request.env['product.template'].sudo().search([('koprol_code', '=', params['product_no_koprol'])], limit=1)

        if product_template and product_template.last_modified_date:
            last_modified_odoo = product_template.last_modified_date
            last_modified_api = datetime.strptime(params['last_modified_koprol'], '%Y-%m-%d %H:%M:%S')
            if last_modified_odoo >= last_modified_api:
                _logger.info(f"Skipping update for product {product_template.name}, Odoo data is newer or same.")
                data = {"product_no_koprol": product_template.koprol_code, "product_no_erp": product_template.default_code}
                return valid_response("success", f"Data Produk tidak diupdate karena data di ERP lebih baru.", data)
        
        try:
            vals = {
                'name': params['product_name'],
                'description': params.get('alias_name'),
                'koprol_code': params['product_no_koprol'],
                'default_code': params.get('product_no_erp') or params['product_no_koprol'],
                'active': params['active_status'],
                'last_modified_date': params['last_modified_koprol'],
                'type': params['product_type'],
                'is_asset': True,
                'is_need_gr': True,
                'sale_ok': False,
                'purchase_ok': True,
            }

            uom_env = request.env['uom.uom'].sudo()
            purchase_uom = uom_env.search([('name', '=', params['purchase_uom'])], limit=1)
            if not purchase_uom:
                return self._log_and_return_error('Failed Master Goods API', url, 404, 'UOM Not Found', f"Purchase UOM '{params['purchase_uom']}' tidak ditemukan.", params)
            vals['uom_po_id'] = purchase_uom.id

            inventory_uom = uom_env.search([('name', '=', params['inventory_uom'])], limit=1)
            if not inventory_uom:
                 return self._log_and_return_error('Failed Master Goods API', url, 404, 'UOM Not Found', f"Inventory UOM '{params['inventory_uom']}' tidak ditemukan.", params)
            vals['uom_id'] = inventory_uom.id

            if params.get('category_code'):
                category = request.env['product.category'].sudo().search([('name', '=', params['category_code'])], limit=1)
                if not category:
                    return self._log_and_return_error('Failed Master Goods API', url, 404, 'Category Not Found', f"Product Category '{params['category_code']}' tidak ditemukan.", params)
                vals['categ_id'] = category.id
                
                asset_category = request.env['account.asset.category'].sudo().search([('name', '=', params['category_code'])], limit=1)
                if asset_category:
                    vals['asset_category_id'] = asset_category.id

            if params.get('default_purchase_tax'):
                tax = request.env['account.tax'].sudo().search([('name', 'ilike', params['default_purchase_tax']), ('type_tax_use', '=', 'purchase')], limit=1)
                if not tax:
                    return self._log_and_return_error('Failed Master Goods API', url, 404, 'Tax Not Found', f"Pajak Pembelian '{params['default_purchase_tax']}' tidak ditemukan.", params)
                vals['supplier_taxes_id'] = [(6, 0, [tax.id])]

            if product_template:
                product_template.sudo().write(vals)
            else:
                product_template = request.env['product.template'].sudo().create(vals)

            data = {"product_no_koprol": product_template.koprol_code, "product_no_erp": product_template.default_code}
            self._log_and_return_error('Success Master Goods API', url, 200, 'success', str(data), params)
            return valid_response("success", "Data Produk Berhasil Disimpan", data)

        except (UserError, ValidationError) as err:
            _logger.error(err); request.env.cr.rollback()
            return self._log_and_return_error('Failed Master Goods API', url, 400, "Validation Error", str(err.name), params)
        except Exception as err:
            _logger.error(err); request.env.cr.rollback()
            return self._log_and_return_error('Failed Master Goods API', url, 500, "Internal Server Error", str(err), params)