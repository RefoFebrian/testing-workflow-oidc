# -*- coding: utf-8 -*-
def _tw_inventory_post_init(env):
    env['res.config.settings'].create({
        'group_stock_tracking_lot': True,  # Activate Packages
        'module_stock_picking_batch': True,  # Activate Batch, Wave & Cluster Transfers
        'group_product_variant': True,  # Activate Product Variant (attribute: color)
        'group_stock_packaging': True,  # Activate Product Packaging
        'group_stock_production_lot': True,  # Activate Lot Serial Numbers
        'group_uom': True,  # Activate Unit of Measure
        'group_lot_on_delivery_slip': True,  # Activate Lot Serial Numbers (Display on slip)
        'group_stock_multi_locations': True,  # Activate Multi Locations
        'group_stock_adv_location': True,  # Activate Multi Route
    }).execute()
    
from . import models
from . import report
from . import controllers
from . import wizard
