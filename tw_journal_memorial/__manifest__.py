# Copyright (C) 2024 Tunas Group
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'TW Journal Memorial',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Journal Memorial Management',
    'description': """
TW Journal Memorial
====================
This module provides functionality for managing journal memorials with approval workflow.

Key Features:
- Create and manage journal memorial entries
- Multi-level approval workflow
- Integration with accounting moves
- Branch-wise configuration
- Auto-reverse functionality
- Period management
""",
    'author': 'Tunas Group',
    'website': 'https://www.tunasgroup.com',
    'depends': [
        'base',
        'account',
        'mail',
        'tw_base',
        'tw_branch',
        'tw_account',
        'tw_account_period',
        'tw_account_setting',
        'om_account_asset',
    ],
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'views/tw_journal_memorial_views.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
