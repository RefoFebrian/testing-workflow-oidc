# 1: imports of python lib
from datetime import date, datetime, timedelta, time

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # 7: defaults methods

    # 8: fields
    type_value = fields.Char('Type', compute='_compute_type_value')

    # 9: relation fields
    part_hotline_id = fields.Many2one('tw.part.hotline', 'No Hotline')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('purchase_order_type_id')
    def _compute_type_value(self):
        for rec in self:
            if rec.purchase_order_type_id:
                rec.type_value = rec.purchase_order_type_id.name.upper().strip()
            else:
                rec.type_value = ''
    
    @api.onchange('purchase_order_type_id')
    def _onchange_hotline(self):
        self.part_hotline_id = False
        if self.purchase_order_type_id:
            if self.purchase_order_type_id.name == 'Hotline':
                picking_type = self.company_id.warehouse_id.in_hotline_type_id
                if not picking_type:
                    raise UserError('Picking Type Incoming untuk Hotline tidak ditemukan pada Warehouse %s !' % self.company_id.warehouse_id.name)
                self.picking_type_id = picking_type.id
    
    @api.onchange('part_hotline_id')
    def _onchange_part_hotline(self):
        self.order_line = False
        if self.part_hotline_id:
            ids = []
            product_category = self.env['product.category'].sudo().search([('name', '=', 'Sparepart')], limit=1)
            if not product_category:
                raise UserError('Product Category Sparepart tidak ditemukan !')
            
            existing_pos = self.part_hotline_id.purchase_order_ids.filtered(lambda po: po.state != 'cancel')
            if getattr(self, '_origin', False) and self._origin.id:
                existing_pos = existing_pos.filtered(lambda po: po.id != self._origin.id)
            po_lines = existing_pos.mapped('order_line')

            for x in self.part_hotline_id.part_detail_ids:
                # Permintaan di Hotline Detail belum terpenuhi
                ordered_qty = sum(po_lines.filtered(lambda line: line.product_id.id == x.product_id.id).mapped('product_qty'))
                total_fulfilled = max(x.qty_po, ordered_qty)
                unfulfilled_qty = x.qty - total_fulfilled

                if unfulfilled_qty > 0:
                    price = 0
                    uom_id = x.product_id.uom_po_id.id
                    pricelist_id = self.order_line._get_pricelist(company=self.company_id)
                    if pricelist_id:
                        price = pricelist_id.with_company(self.company_id.id)._price_get(x.product_id, x.qty or 1.0)[pricelist_id.id]
                    else:
                        price = x.product_id.standard_price
                    
                    supplierinfo = False
                    for supplier in x.product_id.seller_ids:
                        if self.partner_id and (supplier.partner_id.id == self.partner_id.id):
                            supplierinfo = supplier
                            if supplierinfo.product_uom.id != uom_id:
                                raise UserError('The selected supplier only sells this product by %s' % supplierinfo.product_uom.name)
                    
                    dt = self.env['purchase.order.line']._get_date_planned(supplierinfo, self).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    
                    taxes_ids = self.env['account.fiscal.position'].map_tax(x.product_id.supplier_taxes_id)
                    product_qty = unfulfilled_qty
                    if product_qty > 0:
                        ids.append([0, False, {
                            # 'categ_id': product_category.id,
                            'product_id': x.product_id.id,
                            'name': x.product_id.description,
                            'product_qty': product_qty,
                            'price_unit': price,
                            'product_uom': uom_id,
                            'qty_invoiced': 0,
                            # 'received': 0,
                            'taxes_id': [[6, 0, [taxes_ids.id]]],
                            'date_planned': dt,
                            'state': 'draft'
                        }])
            
            if len(ids) > 0:
                self.order_line = ids
            else:
                raise UserError('Detail product sudah tidak ada !')

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        res = super(PurchaseOrder, self).create(vals_list)
        for val in vals_list:
            if 'part_hotline_id' in val:
                part_hotline_obj = self.env['tw.part.hotline'].browse(val['part_hotline_id'])
                if part_hotline_obj:
                    part_hotline_obj.write({'purchase_order_id':res.id})
        return res

    def write(self,vals):
        res = super(PurchaseOrder, self).write(vals)
        if 'part_hotline_id' in self:
            for rec in self:
                if rec.part_hotline_id:
                    rec.part_hotline_id.write({'purchase_order_id': rec.id})
        return res

    # 13: action methods
    def action_view_part_hotline(self):
        if not self.part_hotline_id:
            raise Warning('Part Hotline tidak ditemukan !')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.part.hotline',
            'view_mode': 'form',
            'target': 'current',
            'res_id': self.part_hotline_id.id,
        }