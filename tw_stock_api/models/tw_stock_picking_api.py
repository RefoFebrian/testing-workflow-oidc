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

class InheritApiStockPicking(models.Model):
    _inherit = "stock.picking"

    status_api = fields.Selection([
        ('draft','Draft'),
        ('error','Error'),
        ('done','Done'),
    ], default='draft', string='Status API')

    def schedule_api_stock_picking_to_hoki(self,limit=20):
        return self.api_process_picking(limit)

    def _get_picking_query(self, limit):
        """
        Mengembalikan query SQL untuk semua tipe picking
        :return: string query SQL
        """
        base_query = f"""
            SELECT 
                picking.id as picking_id,
                picking.name as picking_name,
                picking.origin,
                picking.division,
                partner.code as partner_code,
                picking.date,
                CASE
                    WHEN picking.origin LIKE 'SO/%%' THEN 'tw.sale.order'
                    WHEN picking.origin LIKE 'MO/%%' THEN 'tw.mutation.order'
                    ELSE ''
                END as model_name
            FROM stock_picking picking
            INNER JOIN res_company company ON company.id = picking.company_id
            INNER JOIN res_partner partner ON partner.id = picking.partner_id
            INNER JOIN tw_selection branch_type ON branch_type.id = company.branch_type_id
                AND branch_type.type = 'BranchType'
                AND branch_type.value = 'MD'
            WHERE partner.is_send_to_dms = True
            AND picking.state = 'done'
            AND picking.status_api = 'draft'
            AND (picking.origin LIKE 'SO/%%' OR picking.origin LIKE 'MO/%%')
            AND picking.division IN ('Sparepart', 'Unit', 'Umum')
            ORDER BY picking.id ASC
            LIMIT {limit}
        """
        return base_query

    def api_process_picking(self,limit):
        """
        Method utama untuk memproses semua tipe picking
        """
        try:
            query = self._get_picking_query(limit)
            self._cr.execute(query)
            results = self._cr.dictfetchall()
            if not results:
                _logger.warning("Tidak ada data picking yang perlu diproses")
                self._update_error_to_draft()

        except Exception as e:
            message = f'Gagal mendapatkan data picking: {str(e)}'
            _logger.error(message)
            return invalid_response(400, 'Failed to get picking data', message)

        processed_data = []
        success_count = 0
        for result in results:
            res = self._process_picking_data(result)
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
            _logger.warning(f"Data gagal diproses sebanyak {len(results)}")
            return valid_response(200, {
                'total_processed': 0,
                'success_count': 0,
                'failed_count': len(results),
                'message': 'Tidak ada data yang berhasil diproses'
            })

    def _process_picking_data(self, picking_data):
        """
        Memproses data picking
        :param picking_data: dict berisi data picking
        :return: dict berisi status dan pesan
        """
        picking_division = picking_data.get('division')
        module_name = f'TW API STOCK PICKING {picking_division.upper()}'
        
        # Ambil data dari picking_data
        picking_id = picking_data.get('picking_id')
        picking_name = picking_data.get('picking_name')
        picking_origin = picking_data.get('origin')
        model_name = picking_data.get('model_name')
        picking_obj = self.env['stock.picking'].suspend_security().browse(picking_id)
        
        try:
            order_obj = self.env[model_name].suspend_security().search([
                ('name', '=', picking_origin),
                ('stock_distribution_id.model_name', 'in', ['dms.purchase.order.unit', 'dms.purchase.order.sparepart', 'dms.purchase.order.sparepart.hotline']),
                ], limit=1)
            if not order_obj:
                message = f'Stock picking {picking_name} Data Model {model_name} source document {picking_origin} tidak ditemukan!'
                self._log_error(
                    module_name, message,
                    transaction_ids=picking_obj.id,
                    origin=picking_name,
                    payload={'picking_id': picking_obj.id, 'picking_name': picking_name, 'origin': picking_origin, 'model_name': model_name},
                )
                return invalid_response(400, 'Data not found', message)

            return self._process_picking(picking_obj, order_obj, module_name, picking_division)
            
        except Exception as e:
            message = f'Error saat memproses picking {picking_name}: {str(e)}'
            self._log_error(
                module_name, message,
                transaction_ids=picking_obj.id,
                origin=picking_name,
                payload={'picking_id': picking_obj.id, 'picking_name': picking_name, 'origin': picking_origin, 'model_name': model_name},
                response={'error': str(e)},
            )
            return invalid_response(400, 'Terjadi kesalahan saat memproses data picking', message)

    def _process_picking(self, picking_obj, order_obj, module_name, picking_division):
        """
        Method terpadu untuk memproses picking berdasarkan tipe
        
        :param picking_obj: Objek picking yang akan diproses
        :param order_obj: Objek order yang terkait
        :param module_name: Nama modul untuk logging
        :param picking_division: Divisi picking ('Sparepart', 'Unit', atau 'Umum')
        :return: Hasil pemrosesan picking
        """
        try:
            # Ambil data dari distribution
            dms_transaction_id = order_obj.stock_distribution_id.origin_transaction_id
            dms_origin = order_obj.stock_distribution_id.origin
            dms_model_name = order_obj.stock_distribution_id.model_name
            picking_rel_origin = order_obj.name
            branch_code_partner = picking_obj.partner_id.code
            picking_date = picking_obj.date.strftime('%Y-%m-%d') if picking_obj.date else ''
            
            # Siapkan data line items
            lines = []
            pricelist = picking_obj.company_id.branch_setting_id.pricelist_purchase_sparepart_id if picking_division == 'Sparepart' else picking_obj.company_id.branch_setting_id.pricelist_purchase_unit_id
            if not pricelist:
                message = f'Pricelist Harga Jual Part tidak ditemukan untuk {picking_obj.name}'
                self._log_error(
                    module_name, message,
                    transaction_ids=picking_obj.id,
                    origin=picking_obj.name,
                    payload={'picking_id': picking_obj.id, 'picking_name': picking_obj.name, 'division': picking_division},
                )
                return invalid_response(400, 'Data not found', message)
            
            # Proses setiap line picking
            move_line_ids = picking_obj.mapped('move_ids_without_package.move_line_ids')
            for line in move_line_ids:
                price_get = pricelist._price_get(line.product_id.product_tmpl_id, 1)
                price = price_get[pricelist.id] if pricelist.id in price_get else 0
                
                # Tentukan kategori berdasarkan tipe picking
                category = 'unit'  # default
                if line.lot_id and line.lot_id.product_id.product_tmpl_id.categ_id.name == 'EVBT':
                    category = 'battery'
                elif line.lot_id and line.lot_id.product_id.product_tmpl_id.categ_id.name == 'EVCH':
                    category = 'charger'
                
                # Siapkan data line
                line_data = {
                    'product_code': line.product_id.default_code,
                    'qty': line.quantity,
                    'price': price,
                    'tgl_surat_jalan_md': picking_obj.validate_date.strftime('%Y-%m-%d') if picking_obj.validate_date else '',
                }
                if line.lot_id:
                    attribute_color = line.lot_id.product_id.product_template_attribute_value_ids.filtered(
                        lambda x: x.attribute_id.name in ('Color', 'Warna', 'Colour')
                    )
                    color_codes = attribute_color.mapped('product_attribute_value_id.code')
                    # Filter out False/None values dan ambil yang pertama
                    color_code = next((code for code in color_codes if code), '')
                    line_data.update({
                        'no_engine': line.lot_id.name,
                        'chassis_no': line.lot_id.chassis_number,
                        'warna_code': color_code,
                        'tahun_pembuatan': line.production_year if line.production_year else line.lot_id.production_year or '',
                        'no_faktur': line.lot_id.factur_number,
                        'no_ship_list': line.lot_id.ship_list_number,
                        'no_sipb': line.lot_id.sipb_number,
                        'tgl_ship_list': line.lot_id.ship_list_date.strftime('%Y-%m-%d') if line.lot_id.ship_list_date else '',
                        'tgl_receive': line.lot_id.receive_date.strftime('%Y-%m-%d') if line.lot_id.receive_date else '',
                        'tgl_receive_sl': line.lot_id.actual_ssu_md_receive_date.strftime('%Y-%m-%d') if line.lot_id.actual_ssu_md_receive_date else '',
                        'category': category,
                        'qr_code': line.lot_id.qr_code,
                        'accessories_type': line.lot_id.jenis_acc.lower() if line.lot_id.jenis_acc else '',
                    })
                
                lines.append(line_data)
            
            if not lines:
                message = f'Detail line picking {picking_obj.name} kosong!'
                self._log_error(
                    module_name, message,
                    transaction_ids=picking_obj.id,
                    origin=picking_obj.name,
                    payload={'picking_id': picking_obj.id, 'picking_name': picking_obj.name, 'division': picking_division},
                )
                return invalid_response(400, 'Data not found', message)
            
            # Siapkan data untuk API
            api_data = {
                'code_md': picking_obj.company_id.code,
                'branch_code': branch_code_partner,
                'dms_transaction_id': dms_transaction_id,
                'dms_origin': dms_origin,
                'dms_model_name': dms_model_name,
                'origin': picking_rel_origin,
                'surat_jalan': picking_obj.name,
                'division': picking_division,
                'picking_date': picking_date,
                'picking_id': picking_obj.id,
                'line_ids': lines,
            }
            return valid_response(200, api_data, 'Data berhasil diproses')
            
        except Exception as e:
            message = f'Error saat memproses picking {picking_division} {picking_obj.name}: {str(e)}'
            self._log_error(
                module_name, message,
                transaction_ids=picking_obj.id,
                origin=picking_obj.name,
                payload={'picking_id': picking_obj.id, 'picking_name': picking_obj.name, 'division': picking_division},
                response={'error': str(e)},
            )
            return invalid_response(400, 'Terjadi kesalahan saat memproses picking', message)

    def _call_dms_api(self, api_data):
        """Memanggil API DMS dengan data yang telah diproses"""

        module_name = "TW API STOCK PICKING"
        config_obj = self.env['tw.api.configuration'].suspend_security().get_api_config('Hoki')
        if not config_obj:
            message = 'Konfigurasi API untuk sistem Hoki tidak ditemukan'
            self._log_error(
                module_name, message,
                payload=api_data,
            )
            return invalid_response(400, 'Data not found', message)
        
        # Siapkan URL dan headers
        base_url = config_obj.base_url
        url = '/api/stock/v1/create_stock'
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
                self._update_picking_status(transaction_success_ids, 'done')
                if transaction_failed_ids:
                    error_message = data.get('error_message')
                    self._log_error(
                        module_name, error_message,
                        transaction_ids=transaction_failed_ids,
                        url=api_url,
                        payload=api_data,
                        header=headers,
                        response=result,
                        response_code=str(response.status_code),
                        status_code=str(response.status_code),
                    )
                return valid_response(200, api_data, 'Stock picking created successfully')
            else:
                # Log error dari response API
                error_message = data.get('error_descrip')
                self._log_error(
                    module_name, error_message,
                    url=api_url,
                    payload=api_data,
                    header=headers,
                    response=result,
                    response_code=str(response.status_code),
                    status_code=str(response.status_code),
                )
                return invalid_response(400, 'Terjadi kesalahan saat memproses data', error_message)
                
        except requests.exceptions.RequestException as e:
            error_message = f'Gagal memanggil API DMS: {str(e)}'
            self._log_error(
                module_name, error_message,
                url=api_url,
                payload=api_data,
                header=headers,
                response={'error': str(e)},
            )
            return invalid_response(400, 'Terjadi kesalahan saat memproses data', error_message)

    def _log_error(self, module_name, message, transaction_ids=None, origin=None,
                   url=None, payload=None, header=None, response=None,
                   response_code=None, status_code=None):
        """Membuat log error dengan detail payload, header, dan response.
        
        Args:
            module_name (str): Nama modul untuk identifikasi log.
            message (str): Pesan error yang akan dicatat.
            transaction_ids (int/list, optional): ID picking terkait.
            origin (str, optional): Reference/origin document.
            url (str, optional): URL endpoint API.
            payload (dict, optional): Data payload yang dikirim.
            header (dict, optional): Header request API.
            response (dict, optional): Response dari API.
            response_code (str, optional): Kode response API.
            status_code (str, optional): Status code HTTP.
        """
        _logger.warning(message)

        # Gabungkan picking_ids ke dalam response jika ada
        if transaction_ids and not response:
            response = {'picking_ids': transaction_ids}
        elif transaction_ids and isinstance(response, dict):
            response['picking_ids'] = transaction_ids

        self.env['tw.api.log'].suspend_security().create_api_log(
            name=module_name,
            url=url,
            description=str(message),
            ip_address=None,
            response=response or {},
            payload=payload or {},
            header=header or {},
            response_code=response_code,
            status_code=status_code,
            reference=origin,
        )
        # Update status picking ke error
        if transaction_ids:
            self._update_picking_status(transaction_ids, 'error')

    def _update_picking_status(self, transaction_ids, status):
        """Update status picking"""
        picking_objs = self.env['stock.picking'].suspend_security().browse(transaction_ids)
        if picking_objs:
            picking_objs.sudo().write({'status_api': status})

    def _update_error_to_draft(self):
        """
        Update status error ke draft untuk dicoba kembali menggunakan ORM
        """
        error_pickings = self.env['stock.picking'].search([('status_api', '=', 'error')])
        if error_pickings:
            error_pickings.sudo().write({'status_api': 'draft'})


