# -*- coding: utf-8 -*-
{
    'name': "TW Sale Expedition Price",

    'summary': "Connecting Sales to Expedition Price",

    'description': """
        The Expedition Price module in Odoo is used to manage the master pricing of Product at each Branch. 
        With this feature, Companies can ensure Accurate and Efficient Expedition cost estimation across all Branches.
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
    'depends': [
        'base', 
        'base_suspend_security', 
        'tw_sale',
        'tw_pricelist'
        ],

    # always loaded
    'data': [
    ],
    'installable': True,
    'application': True,
}

