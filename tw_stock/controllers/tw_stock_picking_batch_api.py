#!/usr/bin/python
#-*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)

# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response 
from odoo.addons.rest_api.controllers.main import check_valid_token

# 3:  imports of odoo
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request

class ControllerREST(http.Controller):
    def _bad_request(self, info):
        error = 'Bad Request'
        _logger.error(info)
        return invalid_response(400, error, info)

    def _get_expedition_partner(self, expedition_code):
        partner_obj = request.env['res.partner'].sudo()
        domain = [('code', '=', expedition_code)]
        if 'rel_code' in partner_obj._fields:
            domain = ['|', ('code', '=', expedition_code), ('rel_code', '=', expedition_code)]
        return partner_obj.search(domain, limit=1)

    def _get_unit_product(self, product_code, color):
        product_obj = request.env['product.product'].sudo()
        product = product_obj.search([
            '|',
            ('default_code', '=', product_code),
            ('product_tmpl_id.default_code', '=', product_code),
            ('product_template_variant_value_ids.product_attribute_value_id', '=', color.id),
        ], limit=1)
        if product:
            return product

        template = request.env['product.template'].sudo().search([('default_code', '=', product_code)], limit=1)
        if template and hasattr(template, 'get_product_variant'):
            try:
                return template.get_product_variant(product_code, color.code)
            except Exception as err:
                _logger.error(err)

        return product_obj

    def _get_incoming_md_unit_picking_type(self, branch):
        picking_type_obj = request.env['stock.picking.type'].sudo()
        if hasattr(picking_type_obj, 'get_picking_type'):
            try:
                picking_type = picking_type_obj.get_picking_type(
                    'incoming',
                    branch.id,
                    division='Unit',
                    additional_domain=[('sequence_code', '=', 'IN')],
                )
                if picking_type:
                    return picking_type
            except Exception as err:
                _logger.error(err)

        warehouse = request.env['stock.warehouse'].sudo().search([('company_id', '=', branch.id)], limit=1)
        return picking_type_obj.search([
            ('code', '=', 'incoming'),
            ('warehouse_id', '=', warehouse.id),
            ('division', '=', 'Unit'),
            ('sequence_code', '=', 'IN'),
        ], limit=1)

    def _get_unit_move(self, picking_type, branch, product, lot, no_ship_list=False):
        ship_list_number = no_ship_list or getattr(lot, 'ship_list_number', False)
        domain = [
            ('company_id', '=', branch.id),
            ('picking_type_id', '=', picking_type.id),
            ('product_id', '=', product.id),
            ('state', 'in', ['assigned', 'confirmed', 'waiting']),
        ]
        if ship_list_number:
            domain.append(('picking_id.mft_reference', '=', ship_list_number))

        return request.env['stock.move'].sudo().search(domain, order='id', limit=1)

    @http.route('/api/tw_stock/v1/post_create_stock_picking/', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_create_stock_picking(self, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        branch_code = post.get('branch_code')
        ekspedisi = post.get('ekspedisi')
        kota_penerima = post.get('kota_penerima')
        transaksi_for_dms = post.get('transaksi_for_dms')
        packing_line = post.get('packing_line') or []

        if not branch_code:
            return self._bad_request("branch_code harus diisi")

        if not ekspedisi:
            return self._bad_request("ekspedisi harus diisi")

        branch = request.env['res.company'].sudo().search([('code', '=', branch_code)], limit=1)
        if not branch:
            return self._bad_request("invalid data for kode branch [%s]" % (branch_code))

        expedition = self._get_expedition_partner(ekspedisi)
        if not expedition:
            return self._bad_request("invalid data for kode ekspedisi [%s]" % (ekspedisi))

        if not isinstance(packing_line, list) or not packing_line:
            return self._bad_request("packing_line harus diisi")

        picking_type = self._get_incoming_md_unit_picking_type(branch)
        if not picking_type:
            return self._bad_request("Picking Type incoming Unit IN untuk branch [%s] tidak ditemukan" % (branch_code))

        source_picking_ids = set()
        batch_lines = []
        seen_serials = set()

        for data in packing_line:
            no_mesin = data.get('no_mesin')
            product_code = data.get('product_code')
            chassis_number = data.get('chassis_number')
            qty = data.get('qty') or 1
            no_ship_list = data.get('no_ship_list')
            kode_warna = data.get('kode_warna')

            if not no_mesin:
                return self._bad_request("no_mesin harus diisi")
            if not product_code:
                return self._bad_request("product_code harus diisi untuk no mesin [%s]" % (no_mesin))
            if not kode_warna:
                return self._bad_request("kode_warna harus diisi untuk no mesin [%s]" % (no_mesin))
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                return self._bad_request("qty tidak valid untuk no mesin [%s]" % (no_mesin))
            if qty <= 0:
                return self._bad_request("qty harus lebih dari 0 untuk no mesin [%s]" % (no_mesin))

            if no_mesin in seen_serials:
                return self._bad_request("duplicate no mesin [%s]" % (no_mesin))
            seen_serials.add(no_mesin)

            lot = request.env['stock.lot'].sudo().search([('name', '=', no_mesin)], limit=1)
            if not lot:
                return self._bad_request("invalid data for no mesin [%s]" % (no_mesin))

            color = request.env['product.attribute.value'].sudo().search([('code', '=', kode_warna)], limit=1)
            if not color:
                return self._bad_request("invalid data for kode warna [%s]" % (kode_warna))

            product = self._get_unit_product(product_code, color)
            if not product:
                return self._bad_request(
                    "invalid data for product code [%s] & kode warna [%s]" % (product_code, kode_warna)
                )

            if lot.product_id and lot.product_id.id != product.id:
                return self._bad_request(
                    "product code [%s] & kode warna [%s] tidak sesuai dengan no mesin [%s]" %
                    (product_code, kode_warna, no_mesin)
                )

            if no_ship_list and 'ship_list_number' in lot._fields and lot.ship_list_number and lot.ship_list_number != no_ship_list:
                return self._bad_request(
                    "no ship list [%s] tidak sesuai dengan no mesin [%s]" % (no_ship_list, no_mesin)
                )

            move = self._get_unit_move(picking_type, branch, product, lot, no_ship_list=no_ship_list)
            if not move:
                return self._bad_request(
                    "Picking/Move untuk no mesin [%s], product [%s], ship list [%s] tidak ditemukan" %
                    (no_mesin, product_code, no_ship_list or getattr(lot, 'ship_list_number', False))
                )
            source_picking_ids.add(move.picking_id.id)

            vals = {
                'lot_id': lot.id,
                'product_id': product.id,
                'move_id': move.id,
                'location_id': move.location_id.id,
                'quantity': qty,
                'product_uom_qty': move.product_uom_qty,
                'is_rfs': True,
            }
            if chassis_number:
                vals['chassis_number'] = chassis_number
            batch_lines.append((0, 0, vals))

        vals = {
            'company_id': branch.id,
            'picking_type_id': picking_type.id,
            'type': 'MD',
            'division': 'Unit',
            'has_batch_line': True,
            'source_picking_ids': [(6, 0, list(source_picking_ids))],
            'batch_line_ids': batch_lines,
        }
        if 'description' in request.env['stock.picking.batch']._fields:
            vals['description'] = transaksi_for_dms
        if 'partner_id' in request.env['stock.picking.batch']._fields:
            vals['partner_id'] = expedition.id

        try:
            batch = request.env['stock.picking.batch'].sudo().with_company(branch).create(vals)
        except Exception as err:
            request._cr.rollback()
            info = "Gagal Create Stock Picking Batch : %s" % (err)
            _logger.error(err)
            return invalid_response(400, 'Bad Request', info)

        name = "Success Create Stock Picking Batch : %s (%s)" % (transaksi_for_dms, batch.name)
        return valid_response(status=200, data=name)
    
