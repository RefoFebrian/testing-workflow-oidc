# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, timedelta

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockPickingType(models.Model):
    _inherit = "stock.picking.type"
    

    # 14: private methods

    @api.model
    def get_picking_type_asset(self, code, company_id, division='Umum'):
        """Get picking type for asset operations.

        Ensures is_asset context is passed to get_picking_type so the domain
        filters for asset locations instead of excluding them.
        """
        domain_asset = [('default_location_dest_id.type_id.value', '=', 'asset')]
        get_picking_type = self.with_context(is_asset=True).env['stock.picking.type'].get_picking_type(code, company_id, division, True, additional_domain=domain_asset)
        if not get_picking_type:
            company_warehouse_obj = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
            picking_type = company_warehouse_obj._create_or_update_sequences_and_picking_types()
            get_picking_type = picking_type.get('picking_type_asset_id', False)
            if not get_picking_type:
                raise Warning(_("No Picking Type Found for %s on division %s in branch %s with Assets") % (code, division, company_id))

        return get_picking_type