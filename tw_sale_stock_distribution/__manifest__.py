# -*- coding: utf-8 -*-
{
    'name': "TW Sale Stock Distribution",

    'summary': "Connect Sale with Stock Distribution",

    'description': """
        Connect Sale with Stock Distribution
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
    'depends': ['base','base_suspend_security','tw_sale','tw_stock_distribution'],

    # always loaded
    'data': [
    ],
    'installable': True,
    'application': True,
}

