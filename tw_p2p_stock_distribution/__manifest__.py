# -*- coding: utf-8 -*-
{
    'name': "TW P2P Stock Distribution",

    'summary': """
    This module is designed to connect two different modules in the Odoo system, the P2P Purchase Order module and the Stock Distribution module. 
    It is intended to automate the process of stock distribution and enhance the efficiency of the supply chain. 
    """,

    'description': """
    This module is designed to connect two different modules in the Odoo system, the P2P Purchase Order module and the Stock Distribution module. 
    It is intended to automate the process of stock distribution and enhance the efficiency of the supply chain. 
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
    'depends': ['base','tw_base','tw_p2p','tw_stock_distribution'],

    # always loaded
    'data': [
        'views/tw_p2p_stock_distribution_view.xml',
    ],

}

