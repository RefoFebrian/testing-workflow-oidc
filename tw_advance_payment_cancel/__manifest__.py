# -*- coding: utf-8 -*-
{
    'name': "TW Advance Payment Cancel",

    'summary': "TW Advance Payment Cancel",

    'description': """
TW Advance Payment Cancel with approval workflow.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    'depends': ['base', 'tw_base', 'tw_account_setting', 'tw_advance_payment', 'tw_cancellation', 'tw_approval', 'tw_settlement'],

    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/tw_cancellation_handler_data.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_advance_payment_cancel_view.xml',
        'views/tw_menu.xml',
    ],
}
