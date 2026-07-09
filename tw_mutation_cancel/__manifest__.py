# -*- coding: utf-8 -*-
{
    'name': "TW Mutation Order Cancel",

    'summary': "Module to manage and cancel stock mutations in Odoo.",

    'description': """
The `tw_mutation_cancel` module provides functionality to manage and cancel stock mutations in Odoo. 
This module is particularly useful for businesses that need to handle stock adjustments or reverse stock movements efficiently. 
It includes features such as:
- Viewing stock mutation records.
- Canceling specific stock mutations.

This module ensures better control and accuracy in stock management processes.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','tw_base','tw_cancellation','tw_mutation','tw_approval'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'security/res_groups_button.xml',

        'views/tw_mutation_cancel_view.xml',
        'views/tw_menu.xml',

        'data/tw_cancellation_handler_data.xml'
        
    ],
}

