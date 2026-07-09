from odoo import models, fields, api

class TWStockPicking(models.Model):
    _inherit = "stock.picking"

    is_consolidated = fields.Boolean('Is Consolidated',compute='_compute_is_consolidated',store=True)

    @api.depends('move_ids','move_ids.quantity','move_ids.consolidated_qty')
    def _compute_is_consolidated(self):
        for record in self:
            record.is_consolidated = not record.move_ids.filtered(lambda x: x.consolidated_qty != x.quantity and x.division != 'Extras').exists()

    def _get_to_store_picking(self):
        res = super()._get_to_store_picking()
        retail_pickings = self._get_last_route_picking_retail()
        other_supplier_pickings = self._get_last_route_picking_from_other_supplier()
        pickings = retail_pickings + other_supplier_pickings
        unconsolidated_pickings = pickings.filtered(lambda picking: (not picking.is_consolidated))
        to_store_pickings = unconsolidated_pickings + res
        return to_store_pickings

    def _get_to_validate_stored_picking(self):
        res = super()._get_to_validate_stored_picking()
        pickings = self._get_last_route_picking_retail()
        to_validate_pickings = pickings.filtered(lambda picking: (picking.state == 'stored' and picking.is_consolidated))
        consolidated_stored_picking = to_validate_pickings + res
        return consolidated_stored_picking
    
    def _get_last_route_picking_retail(self):
        # Mengambil Picking retail ke MD setempat yang move nya berada di last route
        pickings = self.filtered(
            lambda picking: (
                picking.is_picking_in_retail() 
                and all(move._is_last_move_from_route() and not move.to_refund for move in picking.move_ids_without_package)
            )
        )
        return pickings
        
    def _get_last_route_picking_from_other_supplier(self):
        # Mengambil Picking cabang ke suplier selain dari Main Dealernya.
        warehouse = self.env['stock.warehouse']._get_company_warehouse(self.company_id)
        pickings = self.filtered(
            lambda picking: (
                picking.purchase_id and picking.purchase_id.partner_id.code != picking.company_id.default_supplier_id.code
                and picking.picking_type_id.id in self._get_to_store_picking_type(warehouse)
                and all(move._is_last_move_from_route() and not move.to_refund for move in picking.move_ids_without_package)
            )
        )
        return pickings
    
    def is_picking_in_retail(self):
        self.ensure_one()
        # Check apakah picking ini adalah picking dari pembelian (PO) retail
        md_code = self.env['res.company'].get_default_main_dealer_code()
        warehouse = self.env['stock.warehouse']._get_company_warehouse(self.company_id)
        if all([
            self.company_id.default_supplier_id.code != md_code,
            self.group_id,
            self.picking_type_id.id in self._get_to_store_picking_type(warehouse)
                ]):
            return True
        return False

    def _get_to_store_picking_type(self, warehouse):
        return (warehouse.in_type_id.id, warehouse.store_type_id.id)