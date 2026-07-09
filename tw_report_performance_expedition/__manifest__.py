# -*- coding: utf-8 -*-
{
    'name': "TW Report Performance Expedition",

    'summary': "TW Report Performance Expedition",

    'description': """
Report Performance Expedition
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web_report',
        'tw_base',
        'tw_menu',
        'tw_branch',
        'tw_partner',
        'tw_stock',
        'tw_b2b_file',
        'tw_product',
        'tw_stock_inbound',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'views/tw_report_performance_expedition_view.xml',
        'views/tw_menu.xml',
    ],
}