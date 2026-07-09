# -*- coding: utf-8 -*-
{
    'name': 'TW Stock Document',
    'version': '1.1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Stock Document Management (STNK/BPKB)',
    'description': """
        This module provides stock document tracking for vehicles.
        - Tracks STNK and BPKB documents as line items of stock.lot
        - Manages document state (stock, intransit, customer)
        - Tracks document location
        - Provides inheritance for mutation modules to use stock document selection
    """,
    'author': 'Tunas Honda',
    'company': 'PT. Tunas Dwipa Matra',
    'website': 'https://www.honda-ku.com',
    'depends': [
        'base',
        'stock',
        'tw_base',
        'tw_stock',
        'tw_vehicle_document_location',
        'tw_vehicle_document_receipt',
        'tw_vehicle_document_handover',
        'tw_vehicle_document_mutation',
        'tw_vehicle_document_move',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',
        'views/tw_stock_document_views.xml',
        'views/tw_stock_lot_views.xml',
        'views/tw_mutation_inherit_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

