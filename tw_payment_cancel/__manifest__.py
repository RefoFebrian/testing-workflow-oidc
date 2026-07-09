# -*- coding: utf-8 -*-
{
    'name': "TW Payment Cancel",

    'summary': "Module to manage and handle payment cancellations effectively.",

    'description': """
This module provides functionality to manage the cancellation of payments in Odoo. 
It ensures proper handling of sale order cancellations, maintaining data integrity and providing 
necessary tools for users to process cancellations efficiently. Key features include:
- Streamlined cancellation process for dealer sale orders.
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
    'depends': ['base','tw_base','tw_cancellation','tw_payment','tw_approval','tw_account_setting'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',
        'security/res_groups_button.xml',

        'views/tw_payment_cancel_view.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_menu.xml',

        'data/tw_cancellation_handler_data.xml',
    ],
  
}

