# -*- coding: utf-8 -*-
{
    'name': "TW Asset Barcode",

    'summary': "TW Asset Barcode",

    'description': """
    TW Asset Barcode
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
    'depends': ['base','tw_base','tw_asset_management','stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        
        'views/tw_asset_barcode_view.xml',
        'report/tw_print_label.xml',
        
        'views/tw_menu.xml',
    ],
}

