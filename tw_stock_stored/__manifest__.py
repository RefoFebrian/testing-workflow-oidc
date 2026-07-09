# -*- coding: utf-8 -*-
{
    'name': "TW Stock Stored Picking",

    'summary': "Picking with Stored State, for pending Journal Entry creation",

    'description': """
        Picking with Stored State, for pending Journal Entry creation
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
        'tw_base',
        'tw_stock',
        'tw_stock_extras',
    ],

    # always loaded
    'data': [
        'views/tw_stock_picking_inherit_view.xml',
        'views/tw_stock_picking_batch_inherit_view.xml',
        'views/tw_stock_picking_type_inherit_view.xml',
        'data/tw_cron_data.xml',
        'data/tw_stock_location_data.xml',
    ],
    'installable': True,
    'application': True,
}

