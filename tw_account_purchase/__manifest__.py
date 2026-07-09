# -*- coding: utf-8 -*-
{
    'name': "TW Account Purchase",

    'summary': "Account Purchase",

    'description': """
        Account Purchase
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
    'depends': ['base','tw_base','purchase','tw_account','tw_account_setting','tw_purchase_order'],

    # always loaded
    'data': [
        # 'views/tw_account_move_view.xml',
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_purchase_order_type_view.xml',
    ],
    'installable': True,
    'application': True,
}

