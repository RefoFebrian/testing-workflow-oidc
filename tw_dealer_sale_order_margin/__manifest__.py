# -*- coding: utf-8 -*-
{
    'name': "Tw Dealer Sale Order Margin",

    'summary': "Manage retail sales with margin.",

    'description': """
This module facilitates the management of retail sales for calculation margin.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW Sales',
    'version': '0.1',
    'license': 'AGPL-3',
    'application': False,

    # any module necessary for this one to work correctly
    'depends': ['base', 'tw_base', 'tw_incentive'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'reports/tw_report_margin_dso_view.xml',

        # 'views/tw_dealer_sale_order_inherit_view.xml',
        'views/tw_menu.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}

