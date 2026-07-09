# -*- coding: utf-8 -*-
{
    'name': "TW Disbursement",

    'summary': "Disbursement",

    'description': """
        TW Disbursement
    """,

    'license':'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'account',
        'tw_base',
        'tw_menu',
        'tw_selection',
        'tw_account',
        'tw_account_partner',
        'tw_account_setting',
        'tw_account_period',
        'tw_branch',
        'tw_branch_setting',
        'tw_partner',
        'tw_payment',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_disbursement_view.xml',
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_account_payment_inherit_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
}

