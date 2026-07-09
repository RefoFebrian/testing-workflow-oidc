# -*- coding: utf-8 -*-
{
    'name': "TW Sale Plafond",

    'summary': "Partner Plafond Field Adjustment in Sales Module",

    'description': """
        Partner Plafond Field Adjustment in Sales Module
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales / TW Sales',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','base_suspend_security','tw_sale','tw_partner','tw_stock_distribution'],

    # always loaded
    'data': [
        'views/tw_sale_plafond_view.xml',
        'views/tw_sale_plafond_partner_view.xml'
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
}

