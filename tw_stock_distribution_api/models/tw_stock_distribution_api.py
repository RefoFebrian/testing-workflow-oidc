# -*- coding: utf-8 -*-
# 1: imports of python lib
from datetime import datetime, date
import ast
try:
    import simplejson as json
except ImportError:
    import json
import logging
from time import strptime
import requests
from requests.exceptions import RequestException

# 2: import of known third party lib
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo import http
from odoo.http import request, Response
from odoo.addons.tw_api.controllers.main import valid_response, invalid_response, check_sensitive_value
from odoo.addons.rest_api.controllers.main import check_valid_token, validate_payload

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib

class InheritApiStockDistribution(models.Model):
    _inherit = "tw.stock.distribution"

    status_api = fields.Selection([
        ('draft', 'Draft'),
        ('error', 'Error'),
        ('done', 'Done'),
    ], default='draft', string='Status API')

    def schedule_api_stock_distribution_to_hoki(self, limit=10):
        return self.api_process_stock_distribution(limit)

    def api_process_stock_distribution(self, limit):
        """
        Method utama untuk memproses semua Stock Distribution
        """
        try:
            stock_distribution_obj = self.env['tw.stock.distribution'].search([
                ('company_id.branch_type_id.value', '=', 'MD'),
                ('stock_distribution_ids', '!=', False),
                ('status_api', '=', 'draft'),
                ('state', 'in', ['open', 'done']),
                ('model_name', 'in', ['dms.purchase.order.unit', 'dms.purchase.order.sparepart', 'dms.purchase.order.sparepart.hotline'])
            ], limit=limit)
            if not stock_distribution_obj:
                _logger.warning("Tidak ada data stock distribution yang perlu diproses")
                self._update_error_to_draft()

        except Exception as e:
            message = f'Gagal mendapatkan data stock distribution: {str(e)}'
            _logger.error(message)
            return invalid_response(400, 'Failed to get stock distribution data', message)

        processed_data = []
        success_count = 0
        for result in stock_distribution_obj:
            res = self._process_stock_distribution_data(result)
            if res.get('status') == 1:
                success_count += 1
                if 'data' in res:
                    processed_data.append(res['data'])
        
        if processed_data:
            payload = {
                'total_processed': len(processed_data),
                'data': processed_data
            }
            return self._call_dms_api(payload)
        else:
            _logger.warning(f"Data gagal diproses sebanyak {len(stock_distribution_obj)}")
            return valid_response(200, {
                'total_processed': 0,
                'success_count': 0,
                'failed_count': len(stock_distribution_obj),
                'message': 'Tidak ada data yang berhasil diproses'
            })

    def _process_stock_distribution_data(self, stock_distribution_obj):
        """
        Memproses data stock distribution
        :param stock_distribution_obj: object stock distribution
        :return: dict berisi status dan pesan
        """
        module_name = f'TW API STOCK DISTRIBUTION {stock_distribution_obj.division.upper()}'
        
        try:
            data = {
                'distribution_id': stock_distribution_obj.id,
                'dms_po_name': stock_distribution_obj.origin,
                'dms_model_name': stock_distribution_obj.model_name,
                'division': stock_distribution_obj.division,
            }
            detail_list = []
            for line in stock_distribution_obj.stock_distribution_ids:
                detail_line = {
                    'default_code': line.product_id.default_code,
                    'approved_qty': line.approved_qty,
                }
                if stock_distribution_obj.division == 'Unit':
                    attribute_color = line.product_id.product_template_attribute_value_ids.filtered(
                        lambda x: x.attribute_id.name in ('Color', 'Warna', 'Colour')
                    )
                    color_codes = attribute_color.mapped('product_attribute_value_id.code')
                    # Filter out False/None values dan ambil yang pertama
                    color_code = next((code for code in color_codes if code), '')
                    detail_line['warna_code'] = color_code
                    
                detail_list.append(detail_line)
            
            if detail_list:
                data['line_ids'] = detail_list
            
            if not data:
                message = f'Stock distribution {stock_distribution_obj.name} Data Model {stock_distribution_obj.model_name} tidak ditemukan!'
                self._log_error(module_name, message, stock_distribution_obj.id, stock_distribution_obj.name)
                return invalid_response(400, 'Data not found', message)

            return valid_response(200, data, 'Data berhasil diproses')
            
        except Exception as e:
            message = f'Error saat memproses stock distribution {stock_distribution_obj.name}: {str(e)}'
            self._log_error(module_name, message, stock_distribution_obj.id, stock_distribution_obj.name)
            return invalid_response(400, 'Terjadi kesalahan saat memproses data stock distribution', message)

    def _call_dms_api(self, api_data):
        """Memanggil API DMS dengan data yang telah diproses"""

        module_name = "TW API STOCK DISTRIBUTION (Update Qty Approved)"
        config_obj = self.env['tw.api.configuration'].suspend_security().get_api_config('Hoki')
        if not config_obj:
            message = 'Konfigurasi API untuk sistem Hoki tidak ditemukan'
            self._log_error(module_name, message)
            return invalid_response(400, 'Data not found', message)
        
        # Siapkan URL dan headers
        base_url = config_obj.base_url
        url = '/api/stock_distribution/v1/update_qty_approved'
        api_url = f"{base_url}{url}"
        headers = {
            "Content-Type": "application/json",
            "access_token": config_obj.token
        }
        
        try:
            response = requests.post(
                api_url,
                json=api_data,
                headers=headers
            )
            result = response.json()
            response.raise_for_status()
            
            # Proses hasil response
            data = result.get('data')
            transaction_success_ids = data.get('transaction_success_ids')
            transaction_failed_ids = data.get('transaction_failed_ids')
            if response.status_code == 200:
                # Update status ke done jika berhasil
                self._update_stock_distribution_status(transaction_success_ids, 'done')
                if transaction_failed_ids:
                    error_message = data.get('error_message')
                    self._log_error(module_name, error_message, transaction_failed_ids)
                return valid_response(200, api_data, 'Stock Distribution Updated Successfully')
            else:
                # Log error dari response API
                error_message = data.get('error_descrip')
                self._log_error(module_name, error_message)
                return invalid_response(400, 'Terjadi kesalahan saat memproses data', error_message)
                
        except requests.exceptions.RequestException as e:
            error_message = f'Gagal memanggil API DMS: {str(e)}'
            self._log_error(module_name, error_message)
            return invalid_response(400, 'Terjadi kesalahan saat memproses data', error_message)

    def _log_error(self, module_name, message, transaction_ids=None, origin=None):
        """Membuat log error"""
        _logger.warning(message)
        response = {}
        if transaction_ids:
            response = {'stock_distribution_ids': transaction_ids}
            
        self.env['tw.api.log'].suspend_security().create_api_log(
                name=module_name, url=None, description=str(message), ip_address=None,
                response=response, payload=None, header=None, response_code=None, 
                status_code=None, reference=origin
            )
        # Update status stock distribution ke error
        if transaction_ids:
            self._update_stock_distribution_status(transaction_ids, 'error')

    def _update_stock_distribution_status(self, transaction_ids, status):
        """Update status api stock distribution"""
        stock_distribution_objs = self.env['tw.stock.distribution'].suspend_security().browse(transaction_ids)
        if stock_distribution_objs:
            stock_distribution_objs.sudo().write({'status_api': status})

    def _update_error_to_draft(self):
        """
        Update status error ke draft untuk dicoba kembali menggunakan ORM
        """
        error_stock_distributions = self.env['tw.stock.distribution'].suspend_security().search([('status_api', '=', 'error')])
        if error_stock_distributions:
            error_stock_distributions.sudo().write({'status_api': 'draft'})
