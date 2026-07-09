# -*- coding: utf-8 -*-
{
    'name': "TW Inventory Check",

    'summary': "TW Inventory Check",

    'description': """
        This moudule is used to check product stock in branch
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    "license": "AGPL-3",

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tw_base',
        'tw_menu',
        'product',
        'tw_branch_setting',
        'tw_pricelist_branch',
        'tw_stock',
        'tw_product',
        'tw_selection',
        'web_report'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'security/res_groups.xml',

        'views/tw_pricelist_transient_view.xml',
        'views/tw_loss_demand_view.xml',
        'views/tw_loss_demand_report_view.xml',

        'views/tw_menu.xml',
    ],
}

