# -*- coding: utf-8 -*-
{
    'name': "TW Cancellation",

    'summary': "Module for managing transaction cancellations in Odoo",

    'description': """
The `tw_cancellation` module is designed to streamline and manage the cancellation of transactions within the Odoo system. 
It provides tools for handling cancellation requests and approvals. This module enhances operational efficiency by 
automating and simplifying the cancellation process while maintaining data integrity.
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
    'depends': ['base','tw_base','tw_selection','tw_approval','tw_account_period','tw_account_setting'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',
        'security/ir_rule.xml',

        'views/tw_menu.xml',
        'views/tw_cancellation_view.xml',
        'views/tw_account_setting_view.xml',
    ],
}

