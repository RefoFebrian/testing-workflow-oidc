# -*- coding: utf-8 -*-
{
    'name': "TW Dealer Sale Order Expedition",

    'summary': "Extension module for managing Expedition unit sales in tw_dealer_sale_order.",

    'description': """
        This module extends the functionality of tw_dealer_sale_order to streamline and enhance the management of Expedition unit sales.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': False,

    'depends': ['base', 'tw_dealer_sale_order','tw_account_setting', 'tw_partner'],

    'data': [
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_dealer_sale_order_expedition_view.xml',
    ],
    
}

