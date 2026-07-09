# -*- coding: utf-8 -*-
{
    'name': "TW Invoice Hutang Lain",
    'summary': "Invoice Hutang Lain transaction module.",
    'description': """
        This module provides Invoice Hutang Lain transactions and creates Receive Payment entries.
    """,
    'author': "PT. Tunas Dwipa Matra",
    'website': "https://www.honda-ku.com",
    'category': 'TW',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': False,
    'depends': [
        'base',
        'tw_base',
        'tw_branch',
        'tw_account_setting',
        'tw_sequence',
        'tw_account',
        'tw_payment',
    ],
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'views/tw_menu.xml'
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_invoice_hutang_lain_view.xml',
    ],
}
