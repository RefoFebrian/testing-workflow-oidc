# Copyright (C) 2024 Tunas Group
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'TW Net Off',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Manualy reconcile journal entries',
    'description': """
TW Net Off
====================
This module provides functionality for manually reconciling journal entries.

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
        'tw_journal_memorial',
    ],
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'views/tw_net_off_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
