# -*- coding: utf-8 -*-
{
    'name': "TW MRP Purchase",

    'summary': "Connection between MRP and Purchase Order",

    'description': """
This module enable Purchase Order for Umum Division.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",
    'license': 'LGPL-3',

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'tw_base', 'mrp' ,'tw_mrp','tw_purchase_order', 'tw_menu'],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_purchase_order_view.xml',
        'views/tw_menu.xml',
    ],
}

