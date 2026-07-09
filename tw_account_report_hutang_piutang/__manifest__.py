# -*- coding: utf-8 -*-
{
    'name': "TW Report Hutang dan Piutang",
    'summary': "Report Hutang dan Piutang.",
    'description': """
Report Hutang dan Piutang Module
=====================
This module handles report hutang dan piutang.

Key Features:
- Create and manage report hutang
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
        'tw_payment',
        'tw_menu',
        'tw_selection',
    ],

    # Always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        
        'views/tw_account_report_hutang.xml',
        'views/tw_account_report_piutang.xml',
        'views/tw_menu.xml',
    ],
    
    # Only loaded in demonstration mode
    'demo': [],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}

