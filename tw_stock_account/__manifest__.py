# -*- coding: utf-8 -*-
{
    'name': "TW Stock Account",

    'summary': "Stock Account",

    'description': """
        Stock Account
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
    'depends': ['base','base_suspend_security','stock_account','tw_stock'],

    # always loaded
    'data': [
        'views/tw_stock_lot_account_move_view.xml',
        'views/tw_product_category_view.xml',
        'data/product_category_data.xml',
        'security/res_groups.xml',
    ],
    # TODO: pada saat install module pertama kali, field name & model_id di ir.default tidak ada sehingga menimbulkan error
    # "post_init_hook": "_tw_stock_account_init",
    'installable': True,
    'application': True,
}

