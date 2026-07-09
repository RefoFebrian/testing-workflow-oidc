# -*- coding: utf-8 -*-
{
    'name': "Tw Account Discount",

    'summary': "Module to facilitate discounts in invoices and move entries",

    'description': """
        This module provides functionality to manage and apply discounts on invoices and journal entries. 
        It simplifies the process of handling discounts, ensuring accurate financial records and streamlined operations.
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
    'depends': ['base', 'account', 'product', 'uom', 'tw_base', 'tw_account', 'tw_account_branch', 'tw_branch'],

    # always loaded
    'data': [
        'data/data.xml',

        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_button_groups.xml',
        'security/ir_rule.xml',
        
        'views/tw_account_discount_view.xml',
        'views/tw_account_move_discount_views.xml',
        
        'report/template/tw_account_move_discount_template.xml',

        'views/tw_menu_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

