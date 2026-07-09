# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import datetime

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWStockPickingBatchLine(models.Model):
    _name = "tw.stock.picking.batch.line"
    _description = "Stock Picking Batch Line"
    
    # 7: defaults methods
    def _get_year(self):
        current_year = datetime.now().year
        start_year = 2000
        years_available = []

        for x in reversed(range(start_year, current_year + 1)):
            elem = ("{}".format(x), "{}".format(x))
            years_available.append(elem)

        return years_available

    # 8: fields
    package_number = fields.Char(string='Nomor Kardus', help='Nomor Kardus Sparepart')
    sequence_number = fields.Integer(string="Nomor Index", help="Nomor Index")
    quantity = fields.Integer(string="Quantity", default=1, help="Quantity")
    product_uom_qty = fields.Integer('Product Quantity', help="Quantity of Product for move")
    residual_capacity = fields.Integer(string="Sisa Kapasitas", compute='_compute_residual_capacity', help="Kapasitas Sisa")
    location_capacity = fields.Integer(related='location_dest_id.capacity', string="Total Kapasitas", help="Total Kapasitas Lokasi")
    is_rfs = fields.Boolean(string='RFS', default=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), string='Division', compute='_compute_division', store=True)
    lot_name = fields.Char(string='Nomor Mesin', help='Serial Number for create new lot on Retail scheme')
    chassis_number = fields.Char(string='Nomor Rangka', help='Chassis Number for create new lot on Retail scheme')
    production_year = fields.Selection(_get_year, default=lambda self: datetime.now().strftime('%Y'), string='Tahun Produksi', help='Production Year for create new lot on Retail scheme')
    categ_tracking = fields.Selection(related='product_id.categ_id.tracking', string='Tracking by Category')
    
    # 9: relation fields
    lot_id = fields.Many2one(comodel_name='stock.lot', string="Serial Number")
    lot_ids = fields.Many2many(
        comodel_name='stock.lot', 
        relation='tw_stock_picking_batch_line_lot_rel', column1='batch_line_id', column2='lot_id',
        string="List of Serial Number", 
        compute='_compute_lot_ids')
    product_id = fields.Many2one(comodel_name='product.product', string="Product")
    product_domain_ids = fields.Many2many(
        comodel_name='product.product',
        relation='tw_batch_line_product_rel', column1='batch_line_id', column2='product_id',
        compute='_compute_product_domain_ids',
        string="List of Product")
    move_id = fields.Many2one(comodel_name='stock.move', string="Move")
    location_id = fields.Many2one(comodel_name='stock.location', string="Source Location", help='Source Location for the operation')
    location_dest_id = fields.Many2one(comodel_name='stock.location', string="Destination Location", help='Destination Location for the operation')
    batch_id = fields.Many2one(comodel_name='stock.picking.batch', string="Batch")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('lot_id', 'product_id', 'location_id', 'move_id')
    def _compute_lot_ids(self):
        for record in self:
            search_lot = [
                '|',
                ('company_id', '=', record.batch_id.company_id.id),
                ('company_transfer_id', '=', record.batch_id.company_id.id),
            ]
            if record.batch_id.source_picking_ids and not record.batch_id.is_without_source:
                if record.batch_id.type == 'MD' and record.batch_id.division == 'Unit':
                    source_document = [rec.mft_reference for rec in record.batch_id.source_picking_ids if getattr(rec, 'mft_reference', False)]
                    if source_document:
                        search_lot.extend([('ship_list_number', 'in', source_document), ('state', '=', 'intransit')])
                    else:
                        search_lot.append(('state', '=', 'intransit'))
                else:
                    if record.move_id and record.move_id.restrict_lot_ids:
                        search_lot.append(('state', 'in', ('reserved', 'stock', 'intransit')))
                    else:
                        search_lot.append(('state', '=', 'stock'))
            else:
                search_lot.append(('state', '=', 'intransit'))

            if record.product_id:
                search_lot.append(('product_id', '=', record.product_id.id))
            else:
                search_lot.append(('division', '=', 'Unit'))
                
            if record.location_id:
                search_lot.append(('location_id', '=', record.location_id.id))
            if record.move_id and record.move_id.restrict_lot_ids:
                search_lot.append(('id', 'in', record.move_id.restrict_lot_ids.ids))
            
            lot_ids = self.env['stock.lot'].suspend_security().search(search_lot)
            record.lot_ids = lot_ids

    @api.depends('product_id')
    def _compute_product_domain_ids(self):
        for record in self:
            regular = set()
            batch = record.batch_id
            if batch.source_picking_ids:
                move_objs = self.env['stock.move'].suspend_security().search([
                    ('picking_id', 'in', batch.source_picking_ids.ids),
                    ('state', 'in', ['assigned', 'confirmed', 'waiting'])
                ])
                for move in move_objs:
                    product = move.product_id
                    if product.product_tmpl_id.division != 'Extras':
                        regular.add(product.id)

            record.product_domain_ids = list(regular)

    @api.depends('location_dest_id', 'batch_id.batch_line_ids.location_dest_id')
    def _compute_residual_capacity(self):
        for record in self:
            if not record.location_dest_id:
                record.residual_capacity = 0
                continue
            
            residual = 0
            if record.location_dest_id.capacity > 0:
                residual = record.location_dest_id.residual_capacity
                if record.batch_id and record.batch_id.batch_line_ids:
                    same_location_lines = [
                        line for line in record.batch_id.batch_line_ids.filtered(lambda x: x.product_id.product_tmpl_id.division == 'Unit') 
                        if line.location_dest_id == record.location_dest_id 
                        and line != record
                    ]
                    if same_location_lines:
                        residual = residual - len(same_location_lines)
            
            record.residual_capacity = residual
    
    @api.depends('product_id', 'lot_id')
    def _compute_division(self):
        for record in self:
            record.division = record.product_id.product_tmpl_id.division

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        for record in self:
            record.location_dest_id = False
            if record.lot_id:
                record.quantity = 1
                if record.batch_id.type == 'MD':
                    record.product_id = record.lot_id.product_id
                    location_ids = self.env['stock.quant']._get_location_available_by_product(record.lot_id.product_id, record.batch_id.company_id.id)
                    if location_ids:
                        record.location_dest_id = location_ids[0]
                    else:
                        location_obj = self.env['stock.location'].suspend_security().search([
                            ('company_id', '=', record.batch_id.company_id.id),
                            ('usage', '=', 'internal'),
                            ('residual_capacity', '>', 0),
                        ], limit=1)
                        if location_obj:
                            record.location_dest_id = location_obj.id

    @api.onchange('move_id')
    def _onchange_move_id(self):
        for record in self:
            move = record.move_id
            if not move:
                record.quantity = 0
                record.product_uom_qty = 0
                record.location_id = False
                continue

            record.location_id = move.location_id
            record.product_uom_qty = move.product_uom_qty

            batch = record.batch_id
            if move.product_id.tracking == 'serial':
                record.quantity = 1
            elif batch.is_validate_batch_line and batch.default_qty == 'manual':
                record.quantity = 0
            else:
                record.quantity = move.product_uom_qty

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            record.move_id = False
            if record.batch_id.type == 'Retail':
                record.move_id = False
                record.location_dest_id = record.batch_id.picking_type_id.default_location_dest_id.id

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('package_number'):
                self._validate_package_number(vals.get('package_number'))
        
        return super(TWStockPickingBatchLine, self).create(vals_list)
    
    def write(self, vals):
        if vals.get('package_number'):
            self._validate_package_number(vals.get('package_number'))
        return super(TWStockPickingBatchLine, self).write(vals)

    # 13: action methods

    # 14: private methods
    def _validate_package_number(self, package_number):
        package_obj = self.env['stock.quant.package'].search([('name', '=', package_number)])
        if not package_obj:
            raise Warning(f"Package Number {package_number} Not Found!")
