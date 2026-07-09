# -*- coding: utf-8 -*-
{
    'name': "TW Sale Order API",

    'summary': "TW Sale Order API",

    'description': """
        TW Sale Order API
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_api',
        'tw_base',
        'account',
        'tw_sale',
        'tw_stock_distribution',
        'tw_account',
    ],

    # always loaded
    'data': [
        'data/tw_cron_data.xml',
    ],
}

