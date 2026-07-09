# -*- coding: utf-8 -*-
{
    'name': "TW Account Stock Inbound",

    'summary': "This module manages the recording of accrual journals for expedition invoices related to stock receipts (Stock Inbound)",

    'description': """
This module helps companies record shipping bills as accrual journals, so that costs can be recognized when the goods are received, even though the invoice from the shipping service provider has not been received.
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
    'depends': [
        'base',
        'stock_account',
        'tw_menu',
        'tw_base',
        'tw_selection',
        'tw_stock_inbound',
        'tw_stock',
        'tw_account',
        'tw_account_setting',
        'tw_collecting'
    ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_stock_inbound_inherit_view.xml',
        'views/tw_stock_picking_batch_inherit_view.xml',
        'views/tw_stock_picking_inherit_view.xml',
        'views/tw_stock_lot_inherit_view.xml',
    ],
    
}

