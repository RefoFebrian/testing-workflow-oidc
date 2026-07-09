# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.tools import OrderedSet
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 5: local imports

# 6: Import of unknown third party lib

class InheritPurchaseOrderLineAsset(models.Model):
    _name = "purchase.order.asset.line"
    _inherit = "purchase.order.line" 
    _description = "Purchase Order Asset Line"

    # 7: defaults methods

    # 8: fields
    koprol_id = fields.Char(string='Koprol ID')

    name = fields.Char(string='Name')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    date_planned = fields.Date('Date Planned', default=fields.Date.today(), required=False, copy=False)
    state_gr = fields.Char(string='State',compute='_compute_state_gr')
    qty_invoiced = fields.Float(compute='_compute_qty_asset_invoiced', string="Billed Qty", digits='Product Unit of Measure')
    qty_remaining = fields.Integer(string='Qty Remaining')

    is_cip = fields.Boolean(related="asset_category_id.is_cip",string='CIP')
    is_not_fully_received = fields.Boolean(
        compute='_compute_is_not_fully_received',
        store=True,
        string="Not Fully Received"
    )
    is_asset = fields.Boolean(string='Asset/Prepaid?',related='product_id.is_asset')

    # 9: relation fields   
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True),('categ_id', 'ilike', 'Non-trade')], change_default=True, index='btree_not_null', ondelete='restrict')
    order_id = fields.Many2one('purchase.order.asset', string='Order Reference', index=True, required=True, ondelete='cascade')
    asset_category_id = fields.Many2one('account.asset.category', related="product_id.asset_category_id",string='Asset Category', store=True, help="Asset Category for the operation")
    move_dest_ids = fields.Many2many('stock.move', 'stock_move_created_purchase_line_asset_rel', 'purchase_line_asset_id', 'move_id', 'Downstream moves alt')
    move_ids = fields.One2many('stock.move', 'purchase_line_asset_id', string='Reservation', readonly=True, copy=False)
    product_template_attribute_value_ids = fields.Many2many(related='product_id.product_template_attribute_value_ids', readonly=True)
    product_no_variant_attribute_value_ids = fields.Many2many('product.template.attribute.value', string='Product attribute values that do not create variants', ondelete='restrict')
    taxes_id = fields.Many2many('account.tax', string='Taxes', context={'active_test': False})
    # tax_ids = fields.Many2many(
    #     comodel_name='account.tax',
    #     relation='tw_purchase_order_asset_line_tax', column1='order_id', column2='tax_id',
    #     string="Taxes")


    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('product_id')
    def _compute_display_name(self):
        for record in self:
            description = record.name.split("\n")
            if len(description) > 1:
                record.display_name = f"{record.product_id.name} ({description[1]})"
            else:
                record.display_name = f"{record.product_id.name}"
    
    
    @api.depends('product_qty', 'product_uom', 'company_id', 'order_id.partner_id', 'price_unit')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if line.price_unit > 0:
                line.price_unit = line.price_unit

            if line.product_id and line.product_qty and line.price_unit < 0:
                pricelist = self._get_pricelist(line.order_id.company_id, line.order_id.division)
                product = line.product_id.with_context(pricelist=pricelist.id if pricelist else pricelist, quantity=line.product_qty, date=line.order_id.date_order, uom=line.product_uom.id)
                line.price_unit = self._get_price_unit(pricelist, product)
    
    @api.depends('product_qty', 'qty_received')
    def _compute_is_not_fully_received(self):
        for line in self:
            line.is_not_fully_received = (line.product_qty != line.qty_received)

    def _compute_state_gr(self):
        for record in self:
            record.state_gr = 'Not Fulfilled'
            if record.qty_received > 0 and record.qty_received < record.product_qty:
                record.state_gr = 'Partial Receipt'
            elif record.qty_received == record.product_qty:
                record.state_gr = 'Received'
    
    @api.depends('product_id')
    def _onchange_product_cip(self):
        for line in self:
            if line.product_id and line.is_cip:
                line.product_qty = 1
    
    @api.onchange('product_qty','qty_received')
    def _onchange_qty(self):
        if self.product_qty:
            self.qty_remaining = self.product_qty - self.qty_received
    
    @api.onchange('product_id')
    def _onchange_end_date(self):
        for line in self:
            if line.product_id:
                if not line.order_id.end_date:
                    raise Warning("Silahkan isi End Date Effective Date terlebih dahulu")
                line.date_planned = line.order_id.end_date
            
    # 12: override methods
    def _compute_qty_received(self):
        kit_lines = self.env['purchase.order.asset.line']
        lines_stock = self.filtered(lambda l: l.qty_received_method == 'stock_moves' and l.move_ids and l.state != 'cancel')
        product_by_company = defaultdict(OrderedSet)
        for line in lines_stock:
            product_by_company[line.company_id].add(line.product_id.id)
        kits_by_company = {
            company: self.env['mrp.bom']._bom_find(self.env['product.product'].browse(product_ids), company_id=company.id, bom_type='phantom')
            for company, product_ids in product_by_company.items()
        }
        for line in lines_stock:
            kit_bom = kits_by_company[line.company_id].get(line.product_id)
            if kit_bom:
                moves = line.move_ids.filtered(lambda m: m.state == 'done' and not m.scrapped)
                order_qty = line.product_uom._compute_quantity(line.product_uom_qty, kit_bom.product_uom_id)
                filters = {
                    'incoming_moves': lambda m:
                        m._is_incoming() and
                        (not m.origin_returned_move_id or (m.origin_returned_move_id and m.to_refund)),
                    'outgoing_moves': lambda m:
                        m._is_outgoing() and m.to_refund,
                }
                line.qty_received = moves._compute_kit_quantities(line.product_id, order_qty, kit_bom, filters)
                kit_lines += line
    
    def _compute_qty_asset_invoiced(self):
        for line in self:
            qty = 0.0
            line.qty_invoiced = qty
            if line._origin.id:
                check_gr_collecting = sum(self.env['tw.good.receive.collecting.line'].suspend_security().search([('purchase_order_line_id','=',line._origin.id),('collecting_id.state','=', 'done')]))
                if check_gr_collecting and len(check_gr_collecting > 0):
                    line.qty_invoiced = check_gr_collecting
            

    def _get_price_unit(self, pricelist, product):
        is_asset = self.env.context.get('is_asset', False)
        if is_asset:
            return product.standard_price
        if not pricelist:
             pricelist._get_applicable_rules(product,date)
        price_unit = pricelist.with_company(self.company_id.id)._price_get(product,self.product_qty)[pricelist.id]
        return price_unit
        
    