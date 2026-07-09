# -*- coding: utf-8 -*-
{
    'name': "TW Mutation Request",

    'summary': "Mutation Request Module",

    'description': """
The module manages stock movement between warehouses or locations with features for recording, validation, and tracking.
The process includes transfer requests, approvals, shipping, receiving, and automatic stock updates, ensuring transparency and accuracy in inventory management.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'TW',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'tw_branch',
        'tw_branch_setting',
        'tw_partner_branch',
        'tw_selection',
        'tw_stock',
        'tw_purchase_order',
        # TODO: Cek kebutuhan dependencies ke tw_mutation
        # 'tw_mutation',
        'tw_stock_distribution', 
        'tw_sequence',
        ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'views/tw_mutation_request_view.xml',
        'views/tw_mutation_request_showroom_view.xml',
        'views/tw_mutation_request_workshop_view.xml',
        'views/tw_stock_distribution_inherit_view.xml',
        'views/tw_menu.xml',
    ],
    'application':True,
    'installable':True,
}

