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

    is_portal_done = fields.Boolean(string='Portal Done', copy=False)


class ControllerREST(http.Controller):
    def _sql_text_expression(self, model_name, alias, field_name):
        lang = (request.env.context.get('lang') or 'en_US').replace("'", "''")
        field = request.env[model_name]._fields.get(field_name)
        if field and getattr(field, 'translate', False):
            return "COALESCE(%s.%s->>'%s', %s.%s->>'en_US', '')" % (
                alias, field_name, lang, alias, field_name
            )
        return "COALESCE(%s.%s::text, '')" % (alias, field_name)

    @http.route('/api/tw_portal_api/v1/get_surat_jalan/', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_surat_jalan(self, **params):
        status = params.get('status')
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        if not status or not start_date or not end_date:
            return self._invalid_response(400, 'Error', 'Mandatory [status, start_date, end_date]')

        try:
            start_date = fields.Date.to_date(start_date)
            end_date = fields.Date.to_date(end_date)
            if start_date > end_date:
                return self._invalid_response(400, 'Error', 'start_date tidak boleh lebih besar dari end_date')

            query_where = ""
            if status == 'outstanding':
                query_where += " AND COALESCE(spb.is_portal_done, false) != true"
            else:
                query_where += " AND spb.is_portal_done = true"

            query = """
                SELECT
                    spb.id,
                    COALESCE(spb.name, '') AS surat_jalan,
                    COALESCE(spb.date::text, '') AS tgl_surat_jalan,
                    COALESCE(partner.name, '') AS partner,
                    COALESCE(lot.name, bl.lot_name, '') AS no_mesin,
                    COALESCE(lot.chassis_number, bl.chassis_number, '') AS no_chassis
                FROM stock_picking_batch spb
                INNER JOIN tw_stock_picking_batch_line bl ON bl.batch_id = spb.id
                LEFT JOIN stock_lot lot ON lot.id = bl.lot_id
                INNER JOIN stock_picking_type spt
                    ON spt.id = spb.picking_type_id
                    AND spt.code IN ('outgoing', 'interbranch_out')
                INNER JOIN res_company company ON company.id = spb.company_id
                INNER JOIN tw_selection branch_type
                    ON branch_type.id = company.branch_type_id
                    AND branch_type.type = 'BranchType'
                    AND branch_type.value = 'MD'
                LEFT JOIN LATERAL (
                    SELECT rp.name
                    FROM stock_picking_stock_picking_batch_rel rel
                    INNER JOIN stock_picking picking ON picking.id = rel.stock_picking_id
                    INNER JOIN res_partner rp ON rp.id = picking.partner_id
                    WHERE rel.stock_picking_batch_id = spb.id
                    ORDER BY picking.id ASC
                    LIMIT 1
                ) partner ON TRUE
                WHERE spb.state = 'done'
                AND spb.division = 'Unit'
                AND bl.division = 'Unit'
                AND spb.date >= %%s
                AND spb.date <= %%s
                %s
                ORDER BY spb.name ASC, bl.sequence_number ASC, bl.id ASC
            """ % query_where
            request._cr.execute(query, (start_date, end_date))
            response = request._cr.dictfetchall()

            data = {
                'status': 200,
                'message': 'success',
                'response': response,
            }
            return self._valid_response(status=200, data=data)
        except Exception as err:
            _logger.exception("Failed to get API surat jalan")
            return self._invalid_response(400, 'bad_request', str(err))

    @http.route('/api/tw_portal_api/v1/get_surat_jalan_sparepart/', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_surat_jalan_sparepart(self, **params):
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        partner_id = params.get('partner_id')
        status = params.get('status')

        if not start_date or not end_date:
            return invalid_response(400, 'Error', 'Mandatory [start_date, end_date]')

        if partner_id:
            try:
                partner_id = int(partner_id)
            except Exception:
                return invalid_response(400, 'Error', 'Format parameter partner_id tidak valid')

        try:
            start_date = fields.Date.to_date(start_date)
            end_date = fields.Date.to_date(end_date)
            if start_date > end_date:
                return invalid_response(400, 'Error', 'start_date tidak boleh lebih besar dari end_date')

            query_where = ""
            if status == 'outstanding':
                query_where = " AND COALESCE(spb.is_portal_done, false) != true"
            elif status == 'done':
                query_where = " AND spb.is_portal_done = true"
            if partner_id:
                query_where += " AND partner.id = %s"

            product_name = self._sql_text_expression('product.template', 'pt', 'name')
            picking_type_name = self._sql_text_expression('stock.picking.type', 'spt', 'name')

            query = """
                SELECT
                    spb.id AS packing_id,
                    COALESCE(spb.name, '') AS no_bpb,
                    TO_CHAR(spb.date, 'YYYY-MM-DD') AS tanggal_bpb,
                    COALESCE(mutation_order.name, sale_order.name, picking.origin, '') AS no_so,

                    partner.id AS supplier_id,
                    COALESCE(partner.name, '') AS supplier,

                    spt.id AS picking_type_id,
                    %(picking_type_name)s AS lokasi_gedung,

                    picking.id AS picking_id,
                    COALESCE(picking.name, '') AS no_picking,

                    invoice.id AS invoice_id,
                    COALESCE(invoice.invoice_origin, '') AS invoice_origin,
                    COALESCE(invoice.name, '') AS no_invoice,
                    invoice.company_id AS branch_id,
                    invoice.partner_id AS invoice_partner_id,
                    TO_CHAR(invoice.invoice_date, 'YYYY-MM-DD') AS date_invoice,
                    TO_CHAR(invoice.invoice_date_due, 'YYYY-MM-DD') AS date_due,
                    COALESCE(invoice.amount_untaxed, 0) AS amount_untaxed,
                    COALESCE(discount.discount_cash, 0) AS discount_cash,
                    COALESCE(discount.discount_program, 0) AS discount_program,
                    COALESCE(discount.discount_lain, 0) AS discount_lain,
                    COALESCE(invoice.amount_tax, 0) AS amount_tax,
                    COALESCE(invoice.amount_total, 0) AS amount_total,
                    COALESCE(invoice.amount_residual, 0) AS residual,

                    bl.id AS packing_line_id,
                    bl.product_id,
                    %(product_name)s AS product_name,
                    COALESCE(bl.quantity, 0) AS quantity
                FROM stock_picking_batch spb
                INNER JOIN tw_stock_picking_batch_line bl ON bl.batch_id = spb.id
                LEFT JOIN product_product pp ON pp.id = bl.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN stock_move move ON move.id = bl.move_id
                LEFT JOIN stock_picking picking ON picking.id = move.picking_id
                LEFT JOIN tw_sale_order sale_order ON sale_order.id = picking.sale_order_id
                LEFT JOIN tw_mutation_order mutation_order ON mutation_order.id = picking.mutation_order_id
                LEFT JOIN tw_stock_distribution distribution ON distribution.id = sale_order.stock_distribution_id
                LEFT JOIN res_partner partner
                    ON partner.id = COALESCE(picking.partner_id, sale_order.partner_id, distribution.requester_id)
                INNER JOIN stock_picking_type spt
                    ON spt.id = spb.picking_type_id
                    AND spt.code IN ('outgoing', 'interbranch_out')
                INNER JOIN res_company company ON company.id = spb.company_id
                INNER JOIN tw_selection branch_type
                    ON branch_type.id = company.branch_type_id
                    AND branch_type.type = 'BranchType'
                    AND branch_type.value = 'MD'
                LEFT JOIN LATERAL (
                    SELECT account_move.*
                    FROM account_move
                    WHERE account_move.move_type = 'out_invoice'
                      AND account_move.state != 'draft'
                      AND account_move.division = 'Sparepart'
                      AND (
                            account_move.invoice_origin = sale_order.name
                            OR account_move.ref = sale_order.name
                            OR EXISTS (
                                SELECT 1
                                FROM tw_sale_order_line_invoice_rel sale_line_rel
                                INNER JOIN account_move_line invoice_line
                                    ON invoice_line.id = sale_line_rel.invoice_line_id
                                INNER JOIN tw_sale_order_line sale_line
                                    ON sale_line.id = sale_line_rel.order_line_id
                                WHERE invoice_line.move_id = account_move.id
                                  AND sale_line.order_id = sale_order.id
                            )
                      )
                    ORDER BY account_move.invoice_date ASC, account_move.id ASC
                    LIMIT 1
                ) invoice ON TRUE
                LEFT JOIN LATERAL (
                    SELECT
                        SUM(CASE WHEN account_discount.name = 'Discount Cash' THEN move_discount.amount ELSE 0 END) AS discount_cash,
                        SUM(CASE WHEN account_discount.name = 'Discount Program' THEN move_discount.amount ELSE 0 END) AS discount_program,
                        SUM(CASE WHEN account_discount.name = 'Discount Other' THEN move_discount.amount ELSE 0 END) AS discount_lain
                    FROM account_move_discount move_discount
                    INNER JOIN tw_account_discount account_discount
                        ON account_discount.id = move_discount.discount_id
                    WHERE move_discount.move_id = invoice.id
                ) discount ON TRUE
                WHERE spb.state = 'done'
                AND spb.division = 'Sparepart'
                AND bl.division = 'Sparepart'
                AND spb.date >= %%s
                AND spb.date <= %%s
                %(query_where)s
                ORDER BY spb.date ASC, spb.name ASC, bl.id ASC
            """ % {
                'product_name': product_name,
                'picking_type_name': picking_type_name,
                'query_where': query_where,
            }
            query_params = [start_date, end_date]
            if partner_id:
                query_params.append(partner_id)
            request._cr.execute(query, tuple(query_params))
            response = request._cr.dictfetchall()

            data = {
                'status': 200,
                'message': 'success',
                'response': response,
            }
            return valid_response(status=200, data=data)
        except Exception as err:
            _logger.exception("Failed to get API surat jalan sparepart")
            return invalid_response(400, 'bad_request', str(err))

    @http.route('/api/tw_portal_api/v1/post_surat_jalan_done/', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_surat_jalan_done(self, **post):
        vals = json.loads(request.httprequest.get_data(as_text=True))
        if not isinstance(vals, dict):
            return self._invalid_response(400, 'Error', 'Request body harus berupa JSON object')

        no_surat_jalan = vals.get('no_surat_jalan')
        if not no_surat_jalan:
            return self._invalid_response(400, 'Error', 'Mandatory [no_surat_jalan]')

        try:
            query = """
                SELECT id, state
                FROM stock_picking_batch
                WHERE name = %s
                LIMIT 1
            """
            request._cr.execute(query, (no_surat_jalan,))
            surat_jalan_vals = request._cr.dictfetchall()
            surat_jalan = surat_jalan_vals[0] if surat_jalan_vals else False
            if not surat_jalan:
                info = "No Surat Jalan %s Tidak di Temukan!" % no_surat_jalan
                return invalid_response(400, 'data_not_found', info)

            if surat_jalan['state'] != 'done':
                info = "No Surat Jalan %s dengan State %s belum Done!" % (no_surat_jalan, surat_jalan['state'])
                return invalid_response(400, 'data_not_allow', info)

            update = """
                UPDATE stock_picking_batch
                SET is_portal_done = true
                WHERE id = %s
            """
            request._cr.execute(update, (surat_jalan['id'],))

            name = "Success Update Surat Jalan %s" % no_surat_jalan
            return valid_response(status=200, data=name)
        except Exception as err:
            request._cr.rollback()
            _logger.exception("Failed to update API surat jalan done")
            return invalid_response(400, 'bad_request', str(err))
