# -*- coding: utf-8 -*-
{
    'name': "TW Commission Dealer Sale Order",
    
    'summary': "This module is to create commission for dealer sale order",

    'description': """
This module is to create commission for dealer sale order
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    'application': False,

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_dealer_sale_order','tw_commission','tw_account_setting','l10n_id','tw_account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_dealer_sale_order_inherit_view.xml',
        'views/tw_account_setting_inherit_view.xml',

        'data/data.xml',
    ],
}

