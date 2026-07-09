#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
try:
    import simplejson as json
except ImportError:
    import json

from odoo import fields, http, models
from odoo.http import request
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response
from odoo.addons.rest_api.controllers.main import check_valid_token

_logger = logging.getLogger(__name__)


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    is_portal_sj_draft = fields.Boolean(string='Portal SJ Draft', copy=False)


class ControllerREST(http.Controller):
    def _portal_error(self, error, remark):
        return {
            'status': 0,
            'error': error,
            'remark': remark,
        }

    def _sql_text_expression(self, model_name, alias, field_name):
        lang = (request.env.context.get('lang') or 'en_US').replace("'", "''")
        field = request.env[model_name]._fields.get(field_name)
        if field and getattr(field, 'translate', False):
            return "COALESCE(%s.%s->>'%s', %s.%s->>'en_US', '')" % (
                alias, field_name, lang, alias, field_name
            )
        return "COALESCE(%s.%s::text, '')" % (alias, field_name)

    def _get_existing_batch(self, picking):
        domain = [
            '|',
            ('source_picking_ids', 'in', picking.ids),
            ('picking_ids', 'in', picking.ids),
        ]
        batch = request.env['stock.picking.batch'].sudo().search(domain)
        if not batch and picking.batch_id:
            batch = picking.batch_id
        return batch

    def _get_qty_max(self, picking, move, demand_remaining):
        if picking.picking_type_id.code == 'incoming':
            return demand_remaining

        stock_available = request.env['stock.quant'].sudo().get_stock_available(
            move.product_id.id,
            picking.company_id.id,
            False,
            move.location_id.id,
            include_reserved=True,
            location_dest_id=move.location_dest_id.id,
        )
        return min(demand_remaining, stock_available)

    def _prepare_batch_line_vals(self, picking, batch, product, quantity):
        moves = picking.move_ids_without_package.filtered(
            lambda move: move.product_id.id == product.id and move.state not in ('done', 'cancel')
        ).sorted(key=lambda move: move.id)
        if not moves:
            return self._portal_error(
                'data_not_found',
                'Product %s tidak ditemukan di picking product moves !' % product.name,
            )

        remaining_qty = quantity
        line_vals = []
        existing_qty_by_move = {}
        for line in batch.batch_line_ids.filtered(lambda line: line.move_id):
            existing_qty_by_move[line.move_id.id] = existing_qty_by_move.get(line.move_id.id, 0) + line.quantity

        for move in moves:
            demand_remaining = max(move.product_uom_qty - existing_qty_by_move.get(move.id, 0), 0)
            qty_max = self._get_qty_max(picking, move, demand_remaining)
            if qty_max <= 0:
                continue

            line_qty = min(remaining_qty, qty_max)
            if line_qty <= 0:
                continue

            vals = {
                'product_id': product.id,
                'move_id': move.id,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
                'quantity': line_qty,
                'product_uom_qty': move.product_uom_qty,
            }
            if 'is_rfs' in request.env['tw.stock.picking.batch.line']._fields:
                vals['is_rfs'] = True
            line_vals.append((0, 0, vals))
            remaining_qty -= line_qty

            if remaining_qty <= 0:
                break

        if remaining_qty > 0:
            qty_available = quantity - remaining_qty
            return self._portal_error(
                'error',
                'Quantity melebihi jumlah maksimal %d' % qty_available,
            )

        return line_vals

    @http.route('/api/tw_portal_api/v1/get_packing_so/', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_packing_so(self, **params):
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        if not start_date or not end_date:
            return invalid_response(400, 'Bad Request', "Parameter 'start_date' dan 'end_date' tidak boleh kosong!")

        try:
            start_date = fields.Date.to_date(start_date)
            end_date = fields.Date.to_date(end_date)
            if start_date > end_date:
                return invalid_response(400, 'Bad Request', 'start_date tidak boleh lebih besar dari end_date')

            product_name = self._sql_text_expression('product.template', 'pt', 'name')

            query = """
                SELECT
                    sd.name,
                    COALESCE(mo.name, so.name, '') AS origin,
                    COALESCE(to_char(mo.date, 'YYYY-MM-DD'), to_char(so.date_order::date, 'YYYY-MM-DD'), '') AS date,
                    COALESCE(partner.name, '') AS partner,
                    COALESCE(sd.description, '') AS description,
                    COALESCE(sd.origin, '') AS no_p2p,
                    CONCAT('[', COALESCE(pp.default_code, ''), ']', %(product_name)s) AS product,
                    COALESCE(pp.default_code, '') AS prod_code,
                    %(product_name)s AS prod_name,
                    sdl.approved_qty AS qty,
                    COALESCE(spm.name, sps.name, '') AS picking_name
                FROM tw_stock_distribution sd
                INNER JOIN tw_stock_distribution_line sdl ON sdl.stock_distribution_id = sd.id
                INNER JOIN product_product pp ON pp.id = sdl.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                INNER JOIN res_partner partner ON partner.id = sd.requester_id
                INNER JOIN res_company company ON company.id = sd.company_id
                INNER JOIN tw_selection branch_type ON branch_type.id = company.branch_type_id
                    AND branch_type.type = 'BranchType'
                    AND branch_type.value = 'MD'
                LEFT JOIN tw_mutation_order mo ON mo.stock_distribution_id = sd.id
                LEFT JOIN tw_sale_order so ON so.stock_distribution_id = sd.id
                LEFT JOIN stock_picking spm ON spm.mutation_order_id = mo.id
                LEFT JOIN stock_picking_type sptm ON sptm.id = spm.picking_type_id
                LEFT JOIN stock_picking sps ON sps.sale_order_id = so.id
                LEFT JOIN stock_picking_type spts ON spts.id = sps.picking_type_id
                WHERE (mo.state = 'confirm' OR so.state = 'sale')
                AND sd.division = 'Sparepart'
                AND (
                    (mo.date >= %%s AND mo.date <= %%s)
                    OR (so.date_order::date >= %%s AND so.date_order::date <= %%s)
                )
                AND (spm.state = 'assigned' OR sps.state = 'assigned')
                AND (sptm.code = 'interbranch_out' OR spts.code = 'outgoing')
                AND sdl.approved_qty > 0
                ORDER BY sd.name ASC
            """ % {
                'product_name': product_name,
            }
            request._cr.execute(query, (start_date, end_date, start_date, end_date))
            ress = request._cr.dictfetchall()
            return valid_response(status=200, data=ress)
        except Exception as err:
            _logger.exception("Failed to get API packing SO")
            return invalid_response(400, 'Bad Request', str(err))

    @http.route('/api/tw_portal_api/v1/packing_so_draft', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def packing_so_draft(self, **post):
        vals = json.loads(request.httprequest.get_data(as_text=True))
        try:
            mandatory_fields = ['picking_name', 'detail']
            missing_fields = [field for field in mandatory_fields if field not in vals]
            if missing_fields:
                return self._portal_error(
                    'mandatory_field',
                    'Fields ini tidak ada: %s.' % str(missing_fields),
                )

            picking_name = vals.get('picking_name')
            detail = vals.get('detail') or []
            if not detail:
                return self._portal_error('mandatory_field', 'Detail tidak boleh kosong')
            if not isinstance(detail, list):
                return self._portal_error('mandatory_field', 'Detail harus berupa list')

            picking = request.env['stock.picking'].sudo().search([('name', '=', picking_name)], limit=1)
            if not picking:
                return self._portal_error('data_not_found', 'No picking %s' % picking_name)
            if picking.state != 'assigned':
                return self._portal_error(
                    'data_not_allow',
                    'No Surat Jalan %s, State %s' % (picking_name, picking.state),
                )

            batch = self._get_existing_batch(picking)
            if len(batch) > 1:
                return self._portal_error(
                    'data_not_allow',
                    'No packing lebih dari 1 ! %s' % str(batch.mapped('name')),
                )

            if batch and batch.state != 'draft':
                return self._portal_error('data_not_allow', 'No packing sudah %s' % batch.state)
            if batch and batch.is_portal_sj_draft:
                return self._portal_error(
                    'data_not_allow',
                    'No picking %s sudah melakukan is_portal_sj_draft' % picking.name,
                )

            if not batch:
                batch_vals = {
                    'company_id': picking.company_id.id,
                    'picking_type_id': picking.picking_type_id.id,
                    'type': 'Retail',
                    'division': picking.division,
                    'date': fields.Date.context_today(request.env['stock.picking.batch']),
                    'has_batch_line': True,
                    'source_picking_ids': [(6, 0, picking.ids)],
                }
                if 'description' in request.env['stock.picking.batch']._fields:
                    batch_vals['description'] = picking.origin
                batch = request.env['stock.picking.batch'].sudo().with_company(picking.company_id).create(batch_vals)

            product_quantities = {}
            products_by_id = {}
            for data in detail:
                product_name = data.get('product_name')
                if not product_name:
                    return self._portal_error('mandatory_field', 'Fields ini tidak ada: product_name.')

                product = request.env['product.product'].sudo().search([('name', '=', product_name)], limit=1)
                if not product:
                    return self._portal_error(
                        'data_not_found',
                        'Product name %s ini tidak ada !' % product_name,
                    )

                try:
                    quantity = float(data.get('quantity', 0))
                except (TypeError, ValueError):
                    return self._portal_error('mandatory_field', 'Quantity tidak valid !')

                if quantity <= 0:
                    return self._portal_error('mandatory_field', 'Quantity tidak boleh 0 !')

                product_quantities[product.id] = product_quantities.get(product.id, 0) + quantity
                products_by_id[product.id] = product

            batch_lines = []
            for product_id, quantity in product_quantities.items():
                product = products_by_id[product_id]
                prepared_lines = self._prepare_batch_line_vals(picking, batch, product, quantity)
                if isinstance(prepared_lines, dict):
                    return prepared_lines
                batch_lines += prepared_lines

            if not batch_lines:
                return self._portal_error('mandatory_field', 'Detail tidak boleh kosong')

            batch.sudo().write({
                'batch_line_ids': batch_lines,
                'is_portal_sj_draft': True,
            })
            result = {
                'status': 1,
                'remark': 'Succes update packing',
            }
        except Exception as err:
            request._cr.rollback()
            info = "Gagal Update Packing : %s" % err
            _logger.exception(info)
            return invalid_response(400, 'Bad Request', info)

        return valid_response(status=200, data=result)
