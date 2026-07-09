# -*- coding: utf-8 -*-
{
    'name': 'TW Vehicle Registration Process',
    'version': '1.0',
    'category': 'Document Handling',
    'summary': 'Manages vehicle registration (STNK) processing',
    'description': """
        This module handles the vehicle registration (STNK) process including:
        - STNK processing workflow
        - Integration with vehicle documents
        - Tracking of registration status
    """,
    'author': 'Tunas Honda',
    'website': 'https://www.honda-ku.com',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'base',
        'tw_base',
        'tw_stock',
        'tw_vehicle_document',
    ],

    # Always loaded
    'data': [
        'report/tw_vehicle_registration_process_report_view.xml',
        'report/tw_vehicle_registration_report.xml',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/tw_vehicle_registration_process.xml',
        'views/tw_menu.xml',
        'views/tw_stock_lot_inherit_view.xml',
        'views/tw_change_birojasa.xml',
    ],
    
    # Only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
