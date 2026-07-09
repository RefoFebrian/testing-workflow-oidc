# -*- coding: utf-8 -*-
{
    'name': "TW Purchase Order Approval",

    'summary': "Module to manage and streamline purchase order approvals.",

    'description': """
This module provides functionality to manage the approval process for purchase orders in Odoo. 
It allows users to define approval workflows, set approval limits, and track the status of purchase orders 
throughout the approval process. Key features include: Configurable approval levels and rules

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
    'depends': ['base','tw_base','tw_selection','tw_approval','purchase','tw_purchase_order'],

    # always loaded
    'data': [
        'security/res_groups_button.xml',
        'views/tw_purchase_order_approval_view.xml',
    ]
}

