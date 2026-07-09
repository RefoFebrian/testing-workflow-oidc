from odoo import models, fields, api, _
from datetime import datetime

import pytz


class PrintPickingListStockPicking(models.AbstractModel):
    _name = "report.tw_stock.picking_list_template"
    _description = "Stock Picking Report Picking List"

    def no_urut(self, move_lines):
        """Return enumerated move lines as list of (index, line) tuples."""
        return [(i + 1, line) for i, line in enumerate(move_lines)]

    def waktu_local(self):
        """Return current datetime in user's timezone."""
        user = self.env['res.users'].sudo().browse(self.env.uid)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now_utc = pytz.utc.localize(datetime.now())
        now_local = now_utc.astimezone(tz)
        return now_local.strftime("%d-%m-%Y %H:%M")

    def mutation_order(self, picking):
        """Get dealer/partner info based on picking origin."""
        dealer_name = picking.partner_id or False

        if picking.origin and picking.origin[0:2] == 'MO':
            mo_obj = self.env['tw.mutation.order'].sudo().search([
                ('name', '=', picking.origin),
                ('company_id', '=', picking.company_id.id)
            ], limit=1)
            if mo_obj:
                dealer_name = mo_obj.requester_id
        elif picking.origin and picking.origin[0:2] == 'SO' and picking.company_id.code == 'MML':
            dealer_name = picking.partner_id
        elif picking.origin and picking.origin[0:2] == 'SO' and picking.company_id.code != 'MML':
            dsl_obj = self.env['tw.dealer.sale.order'].sudo().search([
                ('name', '=', picking.origin)
            ], limit=1)
            if dsl_obj:
                dealer_name = dsl_obj.partner_id

        return dealer_name

    def qty_total(self, picking):
        """Calculate total quantity from stock moves."""
        total = 0
        for move in picking.move_ids_without_package:
            total += move.quantity
        return total

    def get_sub(self, branch_id, product_id):
        """Get sub location name for sparepart."""
        query = """
            SELECT 
                sl.complete_name as name
            FROM stock_quant sq
            JOIN stock_location sl 
                ON sl.id = sq.location_id
            WHERE sq.company_id = %s
            AND sq.product_id = %s
            LIMIT 1
        """
        self._cr.execute(query, (branch_id, product_id))
        result = self._cr.fetchone()

        if result:
            return result[0]
        return "-"

    def product_color(self, product):
        """Get color attribute value from product variant."""
        if not product:
            return False
        if isinstance(product, str):
            product = self.env['product.product'].sudo().search([('default_code', '=', product)], limit=1)
        if product:
            for ptav in product.product_template_variant_value_ids:
                if ptav.attribute_id.name and ptav.attribute_id.name.lower() in ('color', 'warna'):
                    return '%s - %s' % (ptav.product_attribute_value_id.code, ptav.product_attribute_value_id.name)
            for ptav in product.product_template_variant_value_ids:
                return '%s - %s' % (ptav.product_attribute_value_id.code, ptav.product_attribute_value_id.name)
        return False

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'no_urut': self.no_urut,
            'waktu_local': self.waktu_local,
            'qty_total': self.qty_total,
            'mutation_order': self.mutation_order,
            'get_sub': self.get_sub,
            'product_color': self.product_color,
        }
