# -*- coding: utf-8 -*-
{
    'name': "TW Collecting Voucher",

    'summary': "TW Collecting Voucher",

    'description': """
        TW Collecting Voucher
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'tw_base',
        'tw_collecting',
        'tw_branch',
        'tw_sequence',
        'tw_account',
        'tw_account_setting',
        'tw_dealer_sale_order_voucher',
        'tw_menu',
    ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'views/tw_collecting_voucher_view.xml',
        'views/tw_account_setting_inherit_view.xml',
        
        'views/tw_menu.xml',
    ],
}

