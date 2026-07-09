# -*- coding: utf-8 -*-
{
    'name': 'TW Vehicle Document Receipt',
    'version': '1.0.0',
    'category': 'Document',
    'summary': 'Vehicle Document Receipt Management (STNK/BPKB)',
    'description': """
        This module provides functionality to manage vehicle document receipts including:
        - STNK (Vehicle Registration) Receipt
        - BPKB (Vehicle Ownership) Receipt
        - Document Location Management
    """,
    'author': 'Tunas Honda',
    'company': 'PT. Tunas Dwipa Matra',
    'website': 'https://www.honda-ku.com',
    'depends': [
        'base',
        'tw_base',
        'stock',
        'tw_vehicle_registration_process',
        'tw_vehicle_document_location',
    ],
    'data': [
        'report/tw_vehicle_document_receipt_report.xml',
        'report/tw_vehicle_registration_receipt_view.xml',
        'report/tw_vehicle_ownership_receipt_view.xml',
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        'views/tw_vehicle_registration_receipt_view.xml',
        'views/tw_vehicle_ownership_receipt_view.xml',
        'views/tw_vehicle_document_location_inherit_view.xml',
        'views/tw_stock_lot_inherit_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
