# -*- coding: utf-8 -*-
{
    'name': "TW Stock Location BTL",

    'summary': "Module linked between Stock Location dan Activity Plan BTL",

    'description': """
        TW Stock Location BTL
    """,

    'license': 'AGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Products / TW Products',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_base',
        'tw_selection',
        'tw_stock'
    ],

    # always loaded
    'data': [
        'data/stock_location_type_btl_data.xml',

        'security/res_groups.xml',

        'views/tw_stock_location_btl_view.xml',
        'views/tw_selection_stock_location_btl_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
}

