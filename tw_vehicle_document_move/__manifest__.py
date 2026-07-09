# -*- coding: utf-8 -*-
{
    'name': 'TW Vehicle Document Move',
    'version': '1.0.0',
    'category': 'Document Handling',
    'summary': 'Vehicle Document Movement Tracking (STNK/BPKB)',
    'description': """
        This module provides tracking for vehicle document movements.
        - Tracks STNK and BPKB document movements
        - Auto-creates movement records from receipts, mutations, and handovers
        - Provides movement history via smart button on vehicles
    """,
    'author': 'Tunas Honda',
    'company': 'PT. Tunas Dwipa Matra',
    'website': 'https://www.honda-ku.com',
    'depends': [
        'base',
        'stock',
        'tw_base',
        'tw_vehicle_document',
        'tw_vehicle_document_location',
        'tw_vehicle_document_receipt',
        'tw_vehicle_document_mutation',
        'tw_vehicle_document_handover',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',

        'views/tw_vehicle_document_move_views.xml',
        'views/tw_stock_lot_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
