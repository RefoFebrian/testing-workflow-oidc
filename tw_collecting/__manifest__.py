# Copyright (C) 2024 Tunas Group
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'TW Collecting / Bulking Move Lines',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Collecting / Bulking Move Line Receivables / Payables',
    'description': """
TW Collecting / Bulking Move Lines
==================================
This module provides functionality for collecting and bulking move lines for receivables and payables.

Key Features:
- Collect and bulk process move lines
- Generate collecting vouchers
- Branch-wise processing
- Integration with accounting moves
""",
    'author': 'Tunas Group',
    'website': 'https://www.tunasgroup.com',
    'depends': [
        'base',
        'account',
        'tw_base',
        'tw_branch',
        'tw_sequence',
        'tw_account',
        'tw_account_setting',
        'tw_menu',
    ],
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'views/tw_collecting_views.xml',
        'views/tw_collecting_ar_ap_views.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_menu.xml',

        'data/tw_account_filter_selection_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
