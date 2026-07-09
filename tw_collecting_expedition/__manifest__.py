# -*- coding: utf-8 -*-
{
    'name': "TW Collecting Expedition",

    'summary': "Separate form for Collecting Expedition with stock inbound relation",

    'description': """
This module provides a separate form for managing Collecting Expedition entries.
It includes stock inbound (m2m), partner (expedition only), date, division, date filter, and description fields.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Accounting',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'account',
        'tw_base',
        'tw_approval',
        'tw_collecting',
        'tw_collecting_approval',
        'tw_stock',
        'tw_stock_inbound',
        'tw_account_stock_inbound',
        'tw_account_setting',
    ],

    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_collecting_expedition_views.xml',
    ],
}
