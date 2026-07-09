# -*- coding: utf-8 -*-
{
    'name': "TW B2B API EV",

    'summary': "Module for EV B2B API",

    'description': """
        Module for EV B2B API
    """,

    'license':'LGPL-3',
    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'base_suspend_security',
        'tw_b2b_api',
        'tw_stock',
        'tw_b2b_file_stock',
        'tw_product',
        'tw_api',
        'tw_base',
        'tw_menu',
        'rest_api'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_b2b_api_ev_view.xml',
        'views/tw_b2b_api_monitoring_ev_view.xml',
        'views/tw_b2b_api_monitoring_reject_ev_view.xml',
        'views/tw_stock_lot_inherit_view.xml',
        'views/tw_menu.xml',
        
        'data/tw_cron_data.xml',
    ],
    'installable': True,
    'application': True,
}

