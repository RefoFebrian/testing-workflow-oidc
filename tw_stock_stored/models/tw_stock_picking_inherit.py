# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwStockStoredStockPickingInherit(models.Model):
    _inherit = "stock.picking"

    # 7: defaults methods  

    # 8: fields
    state = fields.Selection(selection_add=[('stored', 'Stored'),('done',)], ondelete={"stored": "cascade"},
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Stored: The transfer has been Received but the stock valuation is not updated.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled."
    )

    # Audit Trail
    store_check_date = fields.Datetime(string="Store Check Date")
    store_date = fields.Datetime(string="Stored Date")
    store_uid = fields.Many2one('res.users', string="Stored By")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def button_validate(self):
        self._check_valid_picking()
        to_store_picking = self._get_to_store_picking()
        to_validate_picking = self - to_store_picking
        if to_store_picking:
            to_store_picking.action_stored()
        
        if not to_validate_picking:
            return self.env['stock.picking']
        
        for picking in to_validate_picking:
            picking.with_company(picking.company_id)._return_product_from_temporary_location()
            
        return super(TwStockStoredStockPickingInherit, to_validate_picking).button_validate()

    def action_stored(self):
        self._sanity_check()
        self._validate_quantity_against_demand()
        for picking in self:
            if picking.state in ('stored', 'done'):
                continue
            picking._store_product_to_temporary_location()
            picking._store_create_backorder()
            picking.write({
                'state': 'stored',
                'store_date': datetime.now(),
                'store_uid': self.env.user.id
            })
        
    def action_check_stored_picking(self):
        to_validate_picking = self._get_to_validate_stored_picking()
        to_validate_picking.action_validate_stored_picking()

    def action_validate_stored_picking(self):
        for picking in self:
            if picking.state != 'stored':
                continue
            picking.button_validate()
            if picking.batch_id:
                picking.batch_id.action_check_stored_done()
    
    # 14: private methods
    def _validate_quantity_against_demand(self):
        """Validate that quantity does not exceed product_uom_qty (demand)."""
        for picking in self:
            for move in picking.move_ids_without_package:
                if move.quantity > move.product_uom_qty:
                    raise Warning(
                        _("Quantity %s untuk product '%s' tidak boleh lebih besar dari Quantity Seharusnya %s.") 
                        % (move.quantity, move.product_id.display_name, move.product_uom_qty)
                    )

    def _get_to_store_picking(self):
        # Return empty object, this method should be inherited on other module
        picking = self.env['stock.picking']
        return picking

    def _get_to_validate_stored_picking(self):
        # Empty Picking Object
        pickings = self.env['stock.picking']

        # ADD return object. No need to store.
        for picking in self:
            for move in picking.move_ids_without_package:
                if move.to_refund:
                    pickings += picking
                    break
        return pickings

    def _store_product_to_temporary_location(self):
        self.ensure_one()
        temporary_location_id = self.get_temporary_location()
        # qty_to_invoice
        for move in self.move_ids_without_package:
            if move.purchase_line_id.product_id == move.product_id:
                qty_received = (move.purchase_line_id.qty_received or 0) + move.quantity
                move.purchase_line_id.write({'qty_received': qty_received})
                
            # Handle move lines to preserve lot information
            for ml in move.move_line_ids:
                if not ml.lot_id and not ml.lot_name and ml.product_id.lot_valuated and ml.quantity:
                    raise Warning(_("Lot/Serial number is mandatory for product valuated by lot"))

                self._store_create_lot(ml)
                
                # Check if this lot/serial number is already present in the temporary location to avoid duplicate quant additions
                if ml.lot_id and ml.product_id.tracking == 'serial':
                    existing_quant = self.env['stock.quant'].sudo().search([
                        ('product_id', '=', move.product_id.id),
                        ('location_id', '=', temporary_location_id.id),
                        ('lot_id', '=', ml.lot_id.id),
                        ('quantity', '>', 0)
                    ], limit=1)
                    if existing_quant:
                        raise Warning('Stock sementara dengan nomor mesin %s sudah ada pada lokasi sementara!'% (ml.lot_id.name))

                self.env['stock.quant'].sudo()._update_available_quantity(
                    move.product_id, 
                    temporary_location_id, 
                    quantity=ml.quantity, 
                    reserved_quantity=False, 
                    lot_id=ml.lot_id, 
                    package_id=ml.package_id, 
                    owner_id=ml.owner_id
                )

    def _store_create_lot(self, move_line):
        if not move_line.lot_name or move_line.lot_id:
            return

        picking_type = move_line.picking_id.picking_type_id
        if not picking_type.use_create_lots:
            return

        domain = [
            ('product_id', '=', move_line.product_id.id),
            ('name', '=', move_line.lot_name),
            '|', ('company_id', '=', False), ('company_id', '=', move_line.company_id.id)
        ]
        lot = self.env['stock.lot'].search(domain, limit=1)

        if not lot and picking_type.use_create_lots:
            lot_vals = move_line._prepare_new_lot_vals()
            lot = self.env['stock.lot'].create(lot_vals)
        
        if lot:
            move_line.lot_id = lot.id
    
    def _store_create_backorder(self):
        self.ensure_one()
        if self.picking_type_id.create_backorder == 'never':
            return
        moves_todo = self.move_ids.filtered(lambda m: not m.state == 'cancel' or (m.quantity <= 0 and not m.is_inventory))
        # TODO : jika menggunakan move_ids_without_package stock extras tidak tergenerate backorder secara langsung. Coba menggunakan move_ids saja. Jika bermasalah cari cara lain.
        # moves_todo = self.move_ids_without_package.filtered(lambda m: not m.state == 'cancel' or (m.quantity <= 0 and not m.is_inventory))
        moves_todo._check_company()
        backorder_moves = moves_todo._create_backorder()
        if backorder_moves:
            self._create_backorder(backorder_moves)

    def _return_product_from_temporary_location(self):
        self.ensure_one()
        if self.state == 'stored':
            temporary_location_id = self.get_temporary_location()
            for move in self.move_ids_without_package:
                # Handle move lines to preserve lot information
                for ml in move.move_line_ids:
                    quantity = ml.quantity * -1
                    self.env['stock.quant'].sudo()._update_available_quantity(
                        move.product_id, 
                        temporary_location_id, 
                        quantity=quantity, 
                        reserved_quantity=False, 
                        lot_id=ml.lot_id, 
                        package_id=ml.package_id, 
                        owner_id=ml.owner_id
                    )
    
    def get_temporary_location(self):
        self.ensure_one()
        temporary_location_id = self.picking_type_id.temporary_location_id
        if not temporary_location_id:
            warehouse = self.env['stock.warehouse']._get_company_warehouse(self.company_id)
            if warehouse.in_type_id and warehouse.reception_steps != 'one_step':
                temporary_location_id = warehouse.in_type_id.temporary_location_id
                if not temporary_location_id:
                    raise Warning(f"Temporary Location for picking type '{self.picking_type_id.name}' and branch '{self.company_id.name}' not found!")
        return temporary_location_id

    def schedule_validate_picking_stored(self, limit=10):
        stored_picking = self.env['stock.picking'].sudo().search([('state', '=', 'stored')], order='store_check_date asc', limit=limit)
        picking_obj = stored_picking._get_to_validate_stored_picking()
        for picking in stored_picking:
            if picking.id in picking_obj.ids:
                picking.action_validate_stored_picking()
            else:
                picking.write({'store_check_date': datetime.now()})