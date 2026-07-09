# -*- coding: utf-8 -*-
{
    'name': "TW Settlement Cancel",

    'summary': "Module to manage and handle settlement cancellations effectively.",

    'description': """
This module provides functionality to manage the cancellation of settlements in Odoo. 
It ensures proper handling of settlement cancellations, maintaining data integrity and providing 
necessary tools for users to process cancellations efficiently. Key features include:
- Streamlined cancellation process for settlements.
- Payment validation before cancellation.
- Journal reversal automation.
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
    'depends': ['base', 'tw_base', 'tw_cancellation', 'tw_settlement', 'tw_approval', 'tw_account_setting'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/ir_rule.xml',

        'views/tw_settlement_cancel_view.xml',
        'views/tw_account_setting_view.xml',
        'views/tw_menu.xml',

        'data/tw_cancellation_handler_data.xml',
    ],
}
