# -*- coding: utf-8 -*-
{
    'name': "TW Vehicle Document Report",
    'summary': "Vehicle Document Management and Reporting",
    'description': """
        Vehicle Document Management System
        =======================================
        
        This module provides comprehensive reporting for vehicle document management including:
        - STNK/BPKB tracking document
        - Lead time analysis for STNK/BPKB processing
        - STNK stock management
        - BPKB ownership tracking
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'category': 'Reporting',
    'version': '1.0.0',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'base',
        'stock',
        'tw_vehicle_document',
        'tw_birojasa_billing_process'
    ],

    # Always loaded data files
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_vehicle_document_report_view.xml',
        'views/tw_birojasa_billing_process_report_view.xml',
        'views/tw_menu.xml',
    ],
    
    # Demo data (if any)
    'demo': [
        # 'demo/demo.xml',
    ],
    
    # Module installation configuration
    'installable': True,
    'application': False,
    'auto_install': False,
}

