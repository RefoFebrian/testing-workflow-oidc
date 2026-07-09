# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import Counter, defaultdict

# 2: import of known third party lib
from datetime import datetime

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules
from odoo.tools import OrderedSet, format_list, groupby

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockMoveLine(models.Model):
    _inherit = "stock.move.line"
    _description = "Stock Move Line"
    
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
    chassis_number = fields.Char(string='Nomor Rangka', help='Nomor Rangka Kendaraan')
    production_year = fields.Selection(_get_year, 'Tahun Produksi', default=lambda self: datetime.now().strftime('%Y'), help='Tahun Produksi Kendaraan')
    is_rfs = fields.Boolean(string='RFS', default=True)
    is_removeable = fields.Boolean(string='Removeable Line', default=True, help='jika removeable di ceklist, maka line bisa dihapus')
    categ_tracking = fields.Selection(related='product_id.categ_id.tracking', string='Tracking by Category')
    supply_qty = fields.Integer(string='Quantity Supply', help='Quantity Supply')

    # 9: relation fields
    location_qc_id = fields.Many2one('stock.location', string='Location QC')
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number')
    domain_lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        relation='tw_stock_domain_lot_rel', column1='move_id', column2='lot_id',
        compute='_compute_domain_lot_ids',
        string="Domain Lot")
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('lot_id', 'product_id')
    def _compute_domain_lot_ids(self):
        for record in self:
            move = record.move_id
            has_restrict_lots = move and 'restrict_lot_ids' in move._fields and move.restrict_lot_ids
            if has_restrict_lots and move.product_id.division == 'Unit':
                record.domain_lot_ids = [(6, 0, move.restrict_lot_ids.ids)]
            else:
                available_lots = []
                if move.picking_id._is_incoming_md():
                    available_lots = self.env['stock.lot'].suspend_security().search(record._prepare_domain_lot()).ids
                else:
                    available_lots = self.env['stock.quant'].get_available_lot_stock(move.product_id.id, move.company_id.id, move.location_id.id).ids

                record.domain_lot_ids = [(6, 0, available_lots)]
            
    @api.onchange('lot_id')
    def onchange_quantity(self):
        if self.lot_id:
            self.quantity = 1

    @api.onchange('lot_name', 'lot_id')
    def _onchange_serial_number(self):
        """ ### Inherited from Original Odoo Code to enable duplicate lot searching within all companies ### 
        When the user is encoding a move line for a tracked product, we apply some logic to
        help him. This includes:
            - automatically switch `quantity` to 1.0
            - warn if he has already encoded `lot_name` in another move line
            - warn (and update if appropriate) if the SN is in a different source location than selected
        """
        res = {}
        if self.product_id.tracking == 'serial':
            if not self.quantity:
                self.quantity = 1

            message = None
            if self.lot_name or self.lot_id:
                move_lines_to_check = self._get_similar_move_lines() - self
                if self.lot_name:
                    counter = Counter([line.lot_name for line in move_lines_to_check])
                    if counter.get(self.lot_name) and counter[self.lot_name] > 1:
                        message = _('You cannot use the same serial number twice. Please correct the serial numbers encoded.')
                    elif not self.lot_id:
                        lots = self.env['stock.lot'].sudo().search([('name', '=', self.lot_name)])
                        quants = lots.quant_ids.filtered(lambda q: q.quantity != 0 and q.location_id.usage in ['customer', 'internal', 'transit'])
                        if quants:
                            message = _(
                                'Serial number (%(serial_number)s) already exists in location(s): %(location_list)s. Please correct the serial number encoded.',
                                serial_number=self.lot_name,
                                location_list=format_list(self.env, quants.sudo().location_id.mapped('display_name'))
                            )
                elif self.lot_id:
                    counter = Counter([line.lot_id.id for line in move_lines_to_check])
                    if counter.get(self.lot_id.id) and counter[self.lot_id.id] > 1:
                        message = _('You cannot use the same serial number twice. Please correct the serial numbers encoded.')
                    else:
                        # check if in correct source location
                        message, recommended_location = self.env['stock.quant'].sudo()._check_serial_number(
                            self.product_id, self.lot_id, self.company_id, self.location_id, self.picking_id.location_id)
                        if recommended_location:
                            self.location_id = recommended_location
            if message:
                res['warning'] = {'title': _('Warning'), 'message': message}
        return res
    
    @api.onchange('production_year')
    def _check_production_year(self):
        if self.production_year:
            if not self.production_year.isdigit() or len(self.production_year) != 4:
                raise Warning(_("Tahun produksi harus 4 digit angka!"))

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        return super(InheritStockMoveLine, self).create(vals_list)
    
    def write(self, vals):
        return super(InheritStockMoveLine, self).write(vals)
    
    def unlink(self):
        for record in self:
            if not record.is_removeable:
                # is_removeable False jika picking terbentuk dari MFT Sparepart
                raise Warning(f"Cannot delete line {record.move_id.product_id.default_code} with quantity {record.quantity}!")
        return super(InheritStockMoveLine, self).unlink()

    # 13: action methods
  
    # 14: private methods
    def _synchronize_quant(self, quantity, location, action="available", in_date=False, **quants_value):
        """Override: Kontrol package pada quant berdasarkan reception_steps warehouse.

        Untuk divisi Sparepart incoming MD:
        - Package dipertahankan pada quant di lokasi transit (Input, QC).
        - Package di-strip hanya pada step terakhir (destinasi = Stock).

        Intervensi HANYA pada destination call (saat 'package' di-pass dari caller).
        Source calls (unreserve/decrease) tidak diubah agar quant matching tetap benar.

        Timeline pemanggilan di core Odoo _action_done:
        1. (-qty, source, action="reserved") → unreserve, tanpa kwarg 'package'
        2. (-qty, source)                    → decrease available, tanpa kwarg 'package'
        3. (+qty, dest, package=result_pkg)  → increase available, DENGAN kwarg 'package'
        """
        # Hanya intervensi saat caller pass 'package' kwarg (= destination call #3)
        if 'package' in quants_value:
            should_strip_package = True  # Default: strip package dari quant destinasi

            if self.move_id and self.move_id.picking_id:
                picking = self.move_id.picking_id
                if picking.division == 'Sparepart':
                    warehouse = (
                        picking.picking_type_id.warehouse_id
                        or self.env['stock.warehouse']._get_company_warehouse(picking.company_id)
                    )
                    if warehouse:
                        # Cek apakah DESTINASI (location parameter) adalah lokasi final
                        if not self._is_final_stock_location(location, warehouse):
                            # Destinasi masih transit → pertahankan package (apapun yang di-pass caller)
                            should_strip_package = False

            if should_strip_package:
                quants_value['package'] = self.env['stock.quant.package']

        # Source calls ('package' not in quants_value): TIDAK diubah.
        # Core Odoo akan gunakan self.package_id untuk matching quant yang benar.

        return super(InheritStockMoveLine, self.with_context(
            reservation_move_id=self.move_id.id if self.move_id else False
        ))._synchronize_quant(quantity, location, action=action, in_date=in_date, **quants_value)

    def _is_final_stock_location(self, location, warehouse):
        """Tentukan apakah location adalah destinasi final berdasarkan reception_steps.

        Lokasi dianggap NON-FINAL jika termasuk lokasi transit (Input/QC)
        sesuai setting reception_steps pada warehouse.
        Lokasi FINAL = Stock dan child-nya (Shelf, Bin, dll).

        :param location: stock.location record (destinasi)
        :param warehouse: stock.warehouse record
        :return: True jika lokasi adalah destinasi final
        """
        non_final_loc_ids = set()
        if warehouse.reception_steps == 'three_steps':
            non_final_loc_ids = {
                warehouse.wh_input_stock_loc_id.id,
                warehouse.wh_qc_stock_loc_id.id,
            }
        elif warehouse.reception_steps == 'two_steps':
            non_final_loc_ids = {
                warehouse.wh_input_stock_loc_id.id,
            }
        # one_step: tidak ada lokasi transit, semua destinasi internal adalah final

        return location.id not in non_final_loc_ids and location.usage in ('internal',)

    def _prepare_new_lot_vals(self):
        vals = super(InheritStockMoveLine, self)._prepare_new_lot_vals()
        # Validate required fields with conditions
        required_fields = [
            ('production_year', True),
            ('is_rfs', True),
            ('chassis_number', self.categ_tracking == 'serial_chassis'),
        ]
        for field, condition in required_fields:
            if condition and not getattr(self, field):
                raise Warning(_("Silahkan input %s terlebih dahulu") % self._fields[field].string)

        # TODO: HPP harus ambil dari pricelist?
        vals.update({
            'company_id': self.company_id.id,
            'chassis_number': self.chassis_number,
            'production_year': self.production_year,
            'ready_for_sale': 'good' if self.is_rfs else 'not_good',
            'division': 'Unit',
            'state': 'stock',
        })
        
        return vals
    
    def _prepare_domain_lot(self):
        # If you want to add a domain to the lot, use this method to add the domain parameter. append domain from return result of this method
        domain = [
            ('product_id', '=', self.move_id.product_id.id), 
            ('company_id', '=', self.picking_id.company_id.id),
            ('location_id', '=', self.move_id.location_id.id),
        ]
        is_incoming_md = self.picking_id._is_incoming_md()
        if is_incoming_md:
            domain.append(('state', '=', 'intransit'))
        
        return domain
