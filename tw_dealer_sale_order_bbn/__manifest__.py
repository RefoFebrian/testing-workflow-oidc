# -*- coding: utf-8 -*-
{
    'name': "TW Dealer Sale Order BBN",

    'summary': "Extension module for managing ownership unit sales in tw_dealer_sale_order.",

    'description': """
        This module extends the functionality of tw_dealer_sale_order to streamline and enhance the management of ownership unit sales.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': False,

    'depends': ['base', 'tw_dealer_sale_order', 'tw_pricelist_bbn','tw_account_setting', 'tw_partner'],

    'data': [
        'views/tw_account_setting_inherit_view.xml',
        'views/tw_dealer_sale_order_bbn_view.xml',
        'views/tw_stock_lot_inherit_view.xml',
        'reports/template/tw_dealer_sale_order_invoice_report_inherit_template.xml'
    ],
    'demo': [
        'demo/demo.xml',
    ],
    
}

