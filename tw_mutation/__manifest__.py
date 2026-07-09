# -*- coding: utf-8 -*-
{
    'name': "TW Mutation",

    'summary': "Mutation Module",

    'description': """
The module manages stock movement between warehouses or locations with features for recording, validation, and tracking.
The process includes transfer requests, approvals, shipping, receiving, and automatic stock updates, ensuring transparency and accuracy in inventory management.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','stock', 'tw_stock', 'tw_stock_account', 'tw_branch', 'tw_selection', 'tw_stock_distribution', 'tw_branch_setting', 'tw_account_setting'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'views/tw_stock_lot_inherit_view.xml',
        'views/tw_mutation_view.xml',
        'views/tw_stock_distribution_inherit_views.xml',
        'views/res_partner_inherit_views.xml',
        'views/stock_warehouse_views.xml',
        'views/tw_product_category_inherit_view.xml',
        'views/tw_menu.xml',
    ],
    'application':True,
    'installable':True,
}

