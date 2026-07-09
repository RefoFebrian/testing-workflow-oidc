# -*- coding: utf-8 -*-
{
    'name': "TW Vehicle Document Update Data",

    'description': """
Menu Penggantian Data STNK BPKB
    """,
    'license': 'LGPL-3',

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Inventory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_stock','stock','tw_branch','mail','tw_vehicle_document'],

    # always loaded
    'data': [
        'security/ir_rule.xml',
        'security/res_group.xml',
        'security/res_group_button.xml',
        'security/ir.model.access.csv',
        'views/tw_vehicle_document_update_data_views.xml',
        'views/stock_lot_inherit_view.xml',
        'views/tw_menu.xml',
    ],

     # Auto-install
    'auto_install': True,
    'installable': True,
}

