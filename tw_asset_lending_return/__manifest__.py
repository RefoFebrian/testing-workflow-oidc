# -*- coding: utf-8 -*-
{
    'name': "TW Assets Lending Return",

    'summary': """
    This module is used to manage the return of assets that have been lent. It adds a new menu for tracking the return of assets that have been lent.
    """,

    'description': """
    This module is used to manage the return of assets that have been lent. It adds a new menu for tracking the return of assets that have been lent.
    
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
    'depends': ['base','tw_base', 'tw_asset_management', 'om_account_asset','tw_asset_mutation'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_master_rent_reason_asset_view.xml',
        'views/tw_asset_lending_view.xml',
        'views/tw_asset_return_view.xml',
        'views/tw_account_asset_view.xml',

        'views/tw_menu.xml',
    ],
}

