# -*- coding: utf-8 -*-
{
    'name': "TW B2b File Stock",

    'summary': "Connect B2B File with Stock",

    'description': """
        Connect B2B File with Stock
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'stock',
        'tw_stock',
        'tw_stock_stored',
    ],

    # always loaded
    'data': [
        'views/tw_inherit_stock_lot_view.xml',
        'views/tw_inherit_stock_picking_view.xml',
        'data/tw_cron_data.xml',
    ],
    'installable': True,
    'application': True,
}

