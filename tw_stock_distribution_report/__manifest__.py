# -*- coding: utf-8 -*-
{
    'name': "TW Stock Distribution Report",

    'summary': "TW Stock Distribution Report",

    'description': """
        TW Stock Distribution Report
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
        'tw_base',
        'tw_menu',
        'tw_branch',
        'tw_product',
        'tw_partner',
        'tw_stock_distribution',
        'tw_mutation',
        'tw_sale',
        'web_report'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'report/tw_stock_distribution_report_view.xml',
        'report/tw_report_order_fulfillment_view.xml',

        'views/tw_menu_view.xml',

    ],
}

