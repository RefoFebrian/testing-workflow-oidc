# -*- coding: utf-8 -*-
{
    'name': "TW Outstanding Delivery",

    'summary': "Outstanding Delivery",

    'description': """
Outstanding Delivery
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Products / TW Products',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_stock'],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/tw_stock_picking_out_dso_view.xml',
        'views/tw_stock_picking_delivery_gmaps_wizard.xml',
    ],

    'application':True,
    'installable':True,
}

