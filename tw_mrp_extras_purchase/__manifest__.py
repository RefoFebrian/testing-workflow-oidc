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

    'depends': ['base', 'tw_base', 'mrp' , 'tw_mrp', 'tw_mrp_extras'],

    'data': [
        'views/tw_product_category_view.xml',
    ],
}

