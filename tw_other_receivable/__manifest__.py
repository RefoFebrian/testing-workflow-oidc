# -*- coding: utf-8 -*-
{
    'name': "TW Other Receivable",
    'summary': "Other Receivable (Formerly known as DN).",
    'description': """
Other Receivable Module
=====================
This module handles other Receivables with approval workflow.

Key Features:
- Create and manage other Receivables
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
        'tw_account',
        'tw_account_setting',
        'tw_payment',
        'tw_register_kwitansi',
        'tw_menu',
        'tw_selection',
        'tw_attachment',
        'tw_base',
    ],

    # Always loaded
    'data': [
        'security/res_groups.xml',
        'security/res_button_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'report/tw_kwitansi_other_receivable_report.xml',
        'report/tw_other_receivable_report.xml',
        'views/tw_other_receivable_view.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_print_kwitansi_wizard_views.xml',
        'views/tw_menu.xml',
        
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

