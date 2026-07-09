# -*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json
import logging

from odoo import fields, http
from odoo.addons.rest_api.controllers.main import check_valid_token
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response
from odoo.http import request

_logger = logging.getLogger(__name__)


class TwP2pPurchaseOrderApi(http.Controller):
    def _bad_request(self, info):
        _logger.error(info)
        return invalid_response(400, 'Bad Request', info)

    def _get_partner_by_code(self, partner_code):
        partner_obj = request.env['res.partner'].sudo()
        domain = [('code', '=', partner_code)]
        if 'default_code' in partner_obj._fields:
            domain = ['|', ('code', '=', partner_code), ('default_code', '=', partner_code)]
        return partner_obj.search(domain, limit=1)

    def _get_sparepart_product(self, product_code):
        product_obj = request.env['product.product'].sudo()
        product = product_obj.search([
            '|',
            ('default_code', '=', product_code),
            ('product_tmpl_id.default_code', '=', product_code),
        ], limit=1)
        if product:
            return product
        return product_obj.search([('name', '=', product_code)], limit=1)

    def _get_current_period_name(self):
        today = fields.Date.context_today(request.env['tw.p2p.purchase.order'])
        periode = request.env['tw.p2p.periode'].sudo().search([
            ('start_date', '<=', today),
            ('end_date', '>=', today),
            ('active', '=', True),
        ], order='name desc', limit=1)
        if not periode:
            periode = request.env['tw.p2p.periode'].sudo().search([
                ('start_date', '<=', today),
                ('end_date', '>=', today),
            ], order='name desc', limit=1)
        return periode.name

    def _get_additional_sparepart_type(self, branch):
        domain = [
            ('division', '=', 'Sparepart'),
            ('name', '=', 'Additional'),
            '|',
            ('company_id', '=', branch.id),
            ('company_id', '=', False),
        ]
        return request.env['tw.purchase.order.type'].sudo().search(domain, limit=1)

    def _get_qty_available(self, branch_supplier, product):
        if not branch_supplier:
            return 0
        qty_in_picking = request.env['stock.picking'].sudo()._get_qty_picking(
            branch_supplier,
            'Sparepart',
            product.id,
        )
        qty_in_quant = request.env['stock.quant'].sudo().get_stock_available(
            product.id,
            branch_supplier.id,
        )
        return qty_in_quant - qty_in_picking

    @http.route('/api/tw_p2p/v1/create_p2p_aplikasi', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def create_p2p_aplikasi(self, **post):
        try:
            payload = json.loads(request.httprequest.get_data(as_text=True))

            mandatory_fields = ['partner_code', 'line']
            missing_fields = [field for field in mandatory_fields if field not in payload]
            if missing_fields:
                return self._bad_request('Fields ini tidak ada: %s.' % missing_fields)

            partner_code = payload.get('partner_code')
            line_ids = payload.get('line') or []

            if not partner_code:
                return self._bad_request('Fields required harus diisi')
            if not isinstance(line_ids, list) or not line_ids:
                return self._bad_request('Data line tidak boleh kosong')

            partner = self._get_partner_by_code(partner_code)
            if not partner:
                return self._bad_request('Partner Code %s tidak ditemukan' % partner_code)

            branch = partner.company_id
            if not branch:
                return self._bad_request('Branch pada partner %s belum terisi' % partner.display_name)
            if not branch.default_supplier_id:
                return self._bad_request('Default supplier pada branch %s belum terisi' % branch.display_name)

            periode = self._get_current_period_name()
            if not periode:
                return self._bad_request('Periode P2P tidak ditemukan, silahkan cek master Periode P2P')

            type_id = self._get_additional_sparepart_type(branch)
            if not type_id:
                return self._bad_request('Purchase Order Type Sparepart Additional tidak ditemukan')

            line_commands = []
            product_ids = set()
            for line in line_ids:
                if not isinstance(line, dict):
                    return self._bad_request('Format detail line tidak valid')

                missing_line_fields = [field for field in ('product_code', 'qty') if field not in line]
                if missing_line_fields:
                    return self._bad_request('Fields detail ini tidak ada: %s.' % missing_line_fields)

                product_code = line.get('product_code')
                if not product_code:
                    return self._bad_request('Product harus diisi')

                try:
                    qty = int(line.get('qty') or 0)
                except (TypeError, ValueError):
                    return self._bad_request('Qty product %s tidak valid' % product_code)
                if qty <= 0:
                    return self._bad_request('Qty product %s harus lebih besar dari 0' % product_code)

                product = self._get_sparepart_product(product_code)
                if not product:
                    return self._bad_request('Product Code %s tidak ditemukan' % product_code)
                if product.id in product_ids:
                    return self._bad_request('Tidak boleh ada Product yg sama dalam satu transaksi: %s' % product.display_name)
                product_ids.add(product.id)

                line_commands.append((0, 0, {
                    'product_id': product.id,
                    'fix_qty': qty,
                    'qty_available': self._get_qty_available(branch.default_supplier_id.company_id, product),
                }))

            vals = {
                'dealer_id': partner.id,
                'supplier_id': branch.default_supplier_id.id,
                'credit_limit_unit': partner.credit_limit_unit,
                'credit_limit_sparepart': partner.credit_limit_sparepart,
                'division': 'Sparepart',
                'periode_id': periode,
                'description': payload.get('description') or False,
                'purchase_order_type_id': type_id.id,
                'type_name': type_id.name,
                'additional_line_ids': line_commands,
            }
            p2p_order = request.env['tw.p2p.purchase.order'].sudo().with_company(branch).create(vals)
        except Exception as err:
            request._cr.rollback()
            info = "Gagal Create P2P Aplikasi : %s" % err
            _logger.error(err)
            return invalid_response(400, 'Bad Request', info)

        result = {
            'status': 1,
            'data': [{'id': p2p_order.id, 'no_p2p': p2p_order.name}],
        }
        return valid_response(status=200, data=result)
