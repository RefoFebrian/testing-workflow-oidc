# -*- coding: utf-8 -*-
{
    'name': "TW Asset Management Approval",

    'summary': "TW Asset Management Approval",

    'description': """
TW Asset Management Approval
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license':'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_asset_management','tw_purchase_order_approval','tw_approval'],

    # always loaded
    'data': [
        'security/res_groups_button.xml',
        'views/tw_good_receive_approval_view.xml',
        'views/tw_good_receive_collecting_approval_view.xml',
        'views/tw_purchase_order_ga_approval_view.xml'
    ],

}

