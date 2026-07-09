# -*- coding: utf-8 -*-
{
    'name': "TW Asset Disposal",

    'summary': "TW Asset Disposal",

    'description': """
    TW Asset Disposal
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','account','om_account_asset','tw_asset_management','tw_account_setting'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',

        'report/tw_asset_disposal_print.xml',

        'views/tw_asset_disposal_view.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_menu.xml',
    ]
}

