# -*- coding: utf-8 -*-
{
    'name': "TW Stock QR Code",

    'summary': "Stock QR Code",

    'description': """
        Stock QR Code
    """,

    'license':'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_stock',
        'tw_qr_code_unit',
        ],

    # always loaded
    'data': [
        'views/tw_stock_move_inherit_view.xml',
        'views/tw_stock_move_line_inherit_view.xml',
        'views/tw_stock_lot_inherit_view.xml',
        'views/tw_stock_picking_batch_inherit_view.xml',
        'views/tw_stock_picking_type_inherit_view.xml'
    ],
    'installable': True,
    'application': True,
}

