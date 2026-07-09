# -*- coding: utf-8 -*-
{
    'name': "TW Payment Request",
    'summary': "Payment Request (Formerly known as NC).",
    'description': """
Payment Request Module
=====================
This module handles payment requests with approval workflow.

Key Features:
- Create and manage payment requests
- Multi-level approval workflow
- Integration with accounting
- Tax computation
- Document attachment
- Audit trail
    """,

    'author': "Tunas Honda",
    'license': "LGPL-3",
    'website': "https://www.honda-ku.com",
    'category': 'Accounting/Payment',
    'version': '0.1',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'base',
        'hr',
        'tw_account',
        'tw_account_setting',
        'tw_account_filter',
        'tw_payment',
        'tw_menu',
        'tw_selection',
        'tw_base',
        'tw_web',
        'tw_hr',
    ],

    # Always loaded
    'data': [
        'security/res_groups.xml',
        'security/res_button_groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        
        'views/tw_payment_request_view.xml',
        'views/tw_payment_request_type_view.xml',
        'views/tw_account_setting_view.xml',
        'reports/tw_payment_request_report_view.xml',
        'reports/tw_payment_request_pdf_report_template.xml',
        'views/tw_menu.xml',
        
        'data/tw_payment_request_type_data.xml',
        'data/tw_account_filter_selection_data.xml',
    ],
    
    # Only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}

