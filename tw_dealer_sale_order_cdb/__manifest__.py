# -*- coding: utf-8 -*-
{
    'name': "TW Dealer Sale Order CDB",

    'summary': "Extension module for managing CDB data in tw_dealer_sale_order.",

    'description': """
        This module extends the functionality of tw_dealer_sale_order to streamline and enhance the management of CDB data.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': False,

    'depends': ['base', 'tw_dealer_sale_order', 'tw_partner_cdb'],

    'data': [
        'views/tw_dealer_sale_order_inherit_view.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    
}

