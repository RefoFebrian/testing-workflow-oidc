# -*- coding: utf-8 -*-
{
    'name': "TW Report Journal",
    'summary': "Report Journal.",
    'description': """
Report Journal Module
=====================
This module handles report journal with approval workflow.

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
        'tw_base',
        'hr',
        'tw_hr',
        'tw_account',
        'tw_account_setting',
        'tw_account_filter',
        'tw_account_report_filter',
        'tw_payment',
        'tw_menu',
        'tw_selection',
    ],

    # Always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        
        'views/tw_account_report_journal.xml',
        'views/tw_menu.xml',
    ],
    
    # Only loaded in demonstration mode
    'demo': [],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}

