# -*- coding: utf-8 -*-
{
    'name': "TW Stock Partner",

    'summary': "Stock Partner",

    'description': """
        Stock Partner
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
    'depends': ['base','base_suspend_security','tw_stock','tw_partner','tw_stock_inbound'],

    # always loaded
    'data': [
        'views/tw_stock_lot_partner_view.xml',
    ],
    'installable': True,
    'application': True,
}

