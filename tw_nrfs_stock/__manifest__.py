# -*- coding: utf-8 -*-
{
    'name': "TW NRFS Stock",

    'summary': "NRFS Stock",

    'description': """
        NRFS Stock
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
        'stock',
        'tw_selection',
        'tw_nrfs',
        'tw_stock',
        'tw_stock_inbound',
        'tw_vehicle'
        ],

    # always loaded
    'data': [
        'views/tw_nrfs_inherit_view.xml',
        'views/tw_stock_inbound_inherit.xml',
        'views/tw_stock_picking_inherit_view.xml',
        'views/tw_stock_picking_batch_inherit_view.xml',
        'views/tw_master_position_unit_view.xml',
        'views/tw_stock_move_inherit_view.xml',
        'views/tw_stock_move_line_inherit_view.xml',
        'views/tw_menu.xml',
    ],
    'installable': True,
    'application': True,
}

