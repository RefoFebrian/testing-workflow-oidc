# -*- coding: utf-8 -*-
{
    'name': "TW Asset Adjustment",

    'summary': """
This module provides functionality to manage and Adjustments about category, company, number depreciation, purchase value, purchase date 
in Assets (REGAS).
    """,

    'description': """
TW Asset Adjustment
=====================

This module provides functionality to manage and Adjustments about category, company, number depreciation, purchase value, purchase date 
in Assets (REGAS).
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','account','tw_base','tw_asset_management','tw_account_setting','om_account_asset'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_group_buttons.xml',
        'security/ir_rule.xml',
        
        'views/tw_asset_adjustment_view.xml',
        'views/tw_account_settings.xml',
        'views/tw_account_asset_view.xml',
        'views/tw_menu.xml',


    ],
}

