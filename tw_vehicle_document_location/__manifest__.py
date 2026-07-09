# -*- coding: utf-8 -*-
{
    'name': 'TW Vehicle Document Location',
    'version': '1.0.0',
    'category': 'Document Handling',
    'summary': 'Management of Vehicle Document Locations (STNK/BPKB)',
    'description': """
        This module provides functionality to manage vehicle document locations
        including STNK and BPKB document storage locations.
    """,
    'author': 'Tunas Honda',
    'company': 'PT. Tunas Dwipa Matra',
    'website': 'https://www.honda-ku.com',
    'depends': [
        'base',
        'tw_base',
        'stock',
        'tw_vehicle_document',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',
        'views/tw_vehicle_document_location_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
